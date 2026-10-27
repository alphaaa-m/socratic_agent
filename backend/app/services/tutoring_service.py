"""Tutoring service -- Phase 3 (docs Sec 19.5, FR-MSG-*, FR-CNV-*)."""

from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.agents.schemas import AgentState, AgentTurnInput, ProfileSnapshot
from app.core.exceptions import NotFoundError, SessionNotActiveError, TurnConflictError
from app.models import (
    LearnerAssessment,
    LearnerProfile,
    LearningProgress,
    LearningSession,
    Message,
    Subject,
)
from app.schemas.assessment import AssessmentResponse
from app.schemas.common import Page
from app.schemas.message import HintResponse, MessageResponse, SendMessageResponse
from app.schemas.session import SessionStateResponse


@dataclass
class TurnContext:
    """The primitive snapshot passed from the read phase to the agent phase."""

    state: AgentState
    profile: ProfileSnapshot
    subject_id: str
    subject_name: str
    subject_description: str | None
    history: list[dict]
    message_count: int


class TutoringService:
    def __init__(self, db: Session, agent=None, settings=None):
        self.db = db
        self.agent = agent
        self.settings = settings

    def list_messages(self, user, session_id, limit: int = 50, offset: int = 0):
        """FR-CNV-02: conversation in time order with pagination."""
        session = self.db.scalar(
            select(LearningSession.id).where(
                LearningSession.id == session_id,
                LearningSession.user_id == user.id,
            )
        )
        if session is None:
            # A missing session and somebody else's session must be indistinguishable.
            raise NotFoundError("Session not found.")

        filters = [Message.session_id == session_id]
        total = self.db.scalar(select(func.count()).select_from(Message).where(*filters)) or 0
        messages = list(
            self.db.scalars(
                select(Message)
                .where(*filters)
                .order_by(Message.created_at.asc(), Message.id.asc())
                .limit(limit)
                .offset(offset)
            )
        )
        return Page(
            items=[MessageResponse.model_validate(message) for message in messages],
            total=total,
            limit=limit,
            offset=offset,
        )

    def handle_student_message(self, user, session_id, content: str):
        """3-phase flow: read -> agent (no DB) -> one write txn with turn_index guard."""
        context = self._read_context_and_close(user, session_id)
        is_first_turn = context.message_count == 0
        turn = AgentTurnInput(
            kind="question" if is_first_turn else "response",
            student_message=content,
            subject_id=context.subject_id,
            subject_name=context.subject_name,
            subject_description=context.subject_description,
            profile=context.profile,
            state=context.state,
            history=context.history,
            is_first_turn=is_first_turn,
        )

        # The database session has been rolled back before the gateway/LLM call.
        out = self.agent.handle_turn(turn)

        with self.db.begin():
            session = self._lock_active_session(user.id, session_id)
            self._guard_turn_index(session, context.state)
            student_message = Message(
                session_id=session.id,
                sender="student",
                message_type=turn.kind,
                content=content,
            )
            agent_message = Message(
                session_id=session.id,
                sender="agent",
                message_type=out.reply.message_type,
                content=out.reply.message,
                retrieved_chunk_ids=[chunk.chunk_id for chunk in out.retrieved],
            )
            self.db.add_all([student_message, agent_message])
            self.db.flush()
            assessment = self._save_assessment(session, student_message, out)
            session.agent_state = out.new_state.model_dump()
            if is_first_turn:
                session.title = content[:60]
            profile = self._apply_learner_update(user.id, out.learner_update)
            self._touch_progress(user.id, session.subject_id)
            self.db.flush()

        return self._to_response(student_message, agent_message, assessment, out, session, profile)

    def handle_hint_request(self, user, session_id):
        """Hint button: no assessment, saves agent hint + new state."""
        context = self._read_context_and_close(user, session_id)
        turn = AgentTurnInput(
            kind="hint_request",
            student_message="",
            subject_id=context.subject_id,
            subject_name=context.subject_name,
            subject_description=context.subject_description,
            profile=context.profile,
            state=context.state,
            history=context.history,
            is_first_turn=context.message_count == 0,
        )
        out = self.agent.handle_turn(turn)

        with self.db.begin():
            session = self._lock_active_session(user.id, session_id)
            self._guard_turn_index(session, context.state)
            agent_message = Message(
                session_id=session.id,
                sender="agent",
                message_type="hint",
                content=out.reply.message,
                retrieved_chunk_ids=[chunk.chunk_id for chunk in out.retrieved],
            )
            self.db.add(agent_message)
            session.agent_state = out.new_state.model_dump()
            profile = self._apply_learner_update(user.id, out.learner_update)
            self._touch_progress(user.id, session.subject_id)
            self.db.flush()

        return HintResponse(
            agent_message=MessageResponse.model_validate(agent_message),
            session_state=self._session_state(session, profile, out),
        )

    def _read_context_and_close(self, user, session_id) -> TurnContext:
        """Read a consistent, detached turn snapshot and release the connection."""
        try:
            return self._load_context(user, session_id)
        finally:
            # Do not retain a database transaction while the gateway might take
            # seconds (or minutes) to answer.  The write phase opens a new one.
            self.db.rollback()

    def _load_context(self, user, session_id) -> TurnContext:
        """Load the owned, active session and the compact agent input context."""
        session = self.db.scalar(
            select(LearningSession).where(
                LearningSession.id == session_id,
                LearningSession.user_id == user.id,
            )
        )
        if session is None:
            raise NotFoundError("Session not found.")
        if session.status != "active":
            raise SessionNotActiveError()

        profile = self.db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user.id))
        if profile is None:
            raise NotFoundError("Learner profile not found.")
        subject = self.db.get(Subject, session.subject_id)
        if subject is None:
            # The foreign-key constraint normally makes this impossible, but it
            # avoids sending incomplete context to the agent if data is corrupt.
            raise NotFoundError("Subject not found.")

        message_count = self.db.scalar(
            select(func.count()).select_from(Message).where(Message.session_id == session.id)
        ) or 0
        newest_first = list(
            self.db.scalars(
                select(Message)
                .where(Message.session_id == session.id)
                .order_by(Message.created_at.desc(), Message.id.desc())
                .limit(10)
            )
        )
        history = [
            {
                "sender": message.sender,
                "content": message.content,
                "message_type": message.message_type,
            }
            for message in reversed(newest_first)
        ]
        return TurnContext(
            state=AgentState.model_validate(session.agent_state),
            profile=ProfileSnapshot(
                current_level=profile.current_level,
                level_score=profile.level_score,
                assessment_count=profile.assessment_count,
                learning_preferences=profile.learning_preferences,
                weaknesses=profile.weaknesses,
            ),
            subject_id=str(subject.id),
            subject_name=subject.name,
            subject_description=subject.description,
            history=history,
            message_count=message_count,
        )

    def _lock_active_session(self, user_id, session_id) -> LearningSession:
        session = self.db.scalar(
            select(LearningSession)
            .where(LearningSession.id == session_id, LearningSession.user_id == user_id)
            .with_for_update()
        )
        if session is None:
            raise NotFoundError("Session not found.")
        if session.status != "active":
            raise SessionNotActiveError()
        return session

    @staticmethod
    def _guard_turn_index(session: LearningSession, previous_state: AgentState) -> None:
        if session.agent_state.get("turn_index", 0) != previous_state.turn_index:
            raise TurnConflictError()

    def _save_assessment(self, session, student_message, out):
        if out.evaluation is None:
            return None
        assessment = LearnerAssessment(
            session_id=session.id,
            message_id=student_message.id,
            correctness_score=out.evaluation.correctness_score,
            reasoning_score=out.evaluation.reasoning_score,
            confidence_score=out.evaluation.confidence_score,
            difficulty_level=out.difficulty_used,
            misconception=out.evaluation.misconception,
            feedback=out.evaluation.feedback,
            resolves_goal=out.new_state.resolved,
        )
        self.db.add(assessment)
        self.db.flush()
        return assessment

    def _apply_learner_update(self, user_id, learner_update) -> LearnerProfile:
        profile = self.db.scalar(
            select(LearnerProfile).where(LearnerProfile.user_id == user_id).with_for_update()
        )
        if profile is None:
            raise NotFoundError("Learner profile not found.")
        profile.level_score = learner_update.level_score
        profile.assessment_count = learner_update.assessment_count
        profile.current_level = learner_update.current_level
        return profile

    def _touch_progress(self, user_id, subject_id) -> None:
        self.db.execute(
            update(LearningProgress)
            .where(LearningProgress.user_id == user_id, LearningProgress.subject_id == subject_id)
            .values(last_activity_at=func.now())
        )

    def _to_response(self, student_message, agent_message, assessment, out, session, profile):
        return SendMessageResponse(
            student_message=MessageResponse.model_validate(student_message),
            agent_message=MessageResponse.model_validate(agent_message),
            assessment=AssessmentResponse.model_validate(assessment) if assessment else None,
            session_state=self._session_state(session, profile, out),
        )

    @staticmethod
    def _session_state(session, profile, out) -> SessionStateResponse:
        return SessionStateResponse(
            status=session.status,
            difficulty=out.new_state.difficulty,
            hint_level=out.new_state.hint_level,
            resolved=out.new_state.resolved,
            learner_level=profile.current_level,
            rag_status=out.rag_status,
        )
