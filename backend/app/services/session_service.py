"""Session service -- Phase 2 (create/list/get), Phase 6 (end) (FR-SES-*, FR-SUM-*)."""

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.agents.schemas import AgentState
from app.core.exceptions import NotFoundError
from app.models import LearnerProfile, LearningProgress, LearningSession, Subject
from app.schemas.common import Page

# Phase 5 will move this mapping to its level-estimation capability. Keeping it
# here makes the Phase 2 starting rule explicit and easy to test.
START_DIFFICULTY = {
    "beginner": 2,
    "intermediate": 3,
    "advanced": 4,
}


class SessionService:
    def __init__(self, db: Session, agent=None, settings=None):
        self.db = db

    def create(self, user, subject_id) -> LearningSession:
        """FR-SES-01..03: active session, initial agent_state, counters +1."""
        try:
            # This lock prevents retirement between the active check and the
            # session creation transaction.
            subject = self.db.scalar(
                select(Subject)
                .where(Subject.id == subject_id, Subject.is_active.is_(True))
                .with_for_update()
            )
            if subject is None:
                # Do not reveal whether the subject is missing or retired.
                raise NotFoundError("Subject not found.")

            profile = self.db.scalar(
                select(LearnerProfile).where(LearnerProfile.user_id == user.id).with_for_update()
            )
            if profile is None:
                raise NotFoundError("Learner profile not found.")

            learning_session = LearningSession(
                user_id=user.id,
                subject_id=subject.id,
                status="active",
                ended_at=None,
                agent_state=AgentState(
                    difficulty=START_DIFFICULTY[profile.current_level]
                ).model_dump(),
            )
            self.db.add(learning_session)
            self.db.flush()

            profile_update = self.db.execute(
                update(LearnerProfile)
                .where(LearnerProfile.user_id == user.id)
                .values(total_sessions=LearnerProfile.total_sessions + 1)
            )
            if profile_update.rowcount != 1:
                raise NotFoundError("Learner profile not found.")

            # PostgreSQL handles both the uniqueness race and the increment.
            # There is no Python read-modify-write cycle that could lose an
            # update from a second, concurrent start request.
            self.db.execute(
                insert(LearningProgress)
                .values(user_id=user.id, subject_id=subject.id)
                .on_conflict_do_nothing(index_elements=["user_id", "subject_id"])
            )
            self.db.execute(
                update(LearningProgress)
                .where(
                    LearningProgress.user_id == user.id,
                    LearningProgress.subject_id == subject.id,
                )
                .values(
                    topics_attempted=LearningProgress.topics_attempted + 1,
                    last_activity_at=func.now(),
                )
            )
            self.db.commit()
        except Exception:
            # A failed progress operation must undo the session and profile
            # counter changes too.
            self.db.rollback()
            raise

        self.db.refresh(learning_session)
        return learning_session

    def list(self, user, subject_id=None, status=None, limit: int = 20, offset: int = 0) -> Page:
        """FR-HIS-01: own sessions newest first."""
        filters = [LearningSession.user_id == user.id]
        if subject_id is not None:
            filters.append(LearningSession.subject_id == subject_id)
        if status is not None:
            filters.append(LearningSession.status == status)

        total = self.db.scalar(select(func.count()).select_from(LearningSession).where(*filters)) or 0
        items = list(
            self.db.scalars(
                select(LearningSession)
                .where(*filters)
                .order_by(LearningSession.started_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return Page(items=items, total=total, limit=limit, offset=offset)

    def get(self, user, session_id) -> LearningSession:
        session = self.db.scalar(
            select(LearningSession).where(
                LearningSession.id == session_id,
                LearningSession.user_id == user.id,
            )
        )
        if session is None:
            # A missing row and another student's row deliberately look alike.
            raise NotFoundError("Session not found.")
        return session

    def end_session(self, user, session_id):
        """FR-SUM-01..04: summary LLM then one write transaction (fallback on failure)."""
        raise NotImplementedError("TODO(phase-6): end session + summary + mastery update")

    def get_summary(self, user, session_id):
        raise NotImplementedError("TODO(phase-6): read saved session summary")
