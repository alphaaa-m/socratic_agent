"""SocraticAgent facade.

Phase 3 deliberately keeps this facade small.  The service supplies all of the
data it needs, so this module remains independent from SQLAlchemy and the
database models.
"""

from app.agents.schemas import (
    AgentTurnInput,
    AgentTurnOutput,
    LearnerUpdate,
    TutorReply,
)


class SocraticAgent:
    def __init__(self, gateway, retriever, settings):
        self.gateway = gateway
        self.retriever = retriever
        self.settings = settings
        # Capability wiring happens in Phase 4/5; keep attribute names stable for tests.
        self.dialogue = None
        self.evaluator = None
        self.adaptive = None
        self.levels = None
        self.hints = None
        self.memory = None
        self.prompts = None
        self.misconceptions = None
        self.summarizer = None

    def handle_turn(self, turn: AgentTurnInput) -> AgentTurnOutput:
        """Generate the deterministic Phase 3 reply through the configured gateway.

        This is intentionally only the thin gateway adapter needed to exercise
        the production turn transaction.  Evaluation, adaptive learning,
        prompts, and retrieval are introduced in the full Phase 4 pipeline.
        """
        # TODO(phase-4): replace with the full pipeline
        state = turn.state.model_copy(deep=True)
        if turn.kind == "question" and turn.is_first_turn:
            state.core_question = turn.student_message
        if turn.kind == "hint_request":
            state.hint_level = min(3, state.hint_level + 1)
            state.hints_used += 1

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": f"You are a concise Socratic tutor for {turn.subject_name}.",
            }
        ]
        for message in turn.history:
            messages.append(
                {
                    "role": "user" if message["sender"] == "student" else "assistant",
                    "content": message["content"],
                }
            )
        if turn.kind == "hint_request":
            messages.append({"role": "user", "content": "Please provide the next hint."})
        else:
            messages.append({"role": "user", "content": turn.student_message})

        reply = self.gateway.generate_reply(messages)
        if turn.kind == "hint_request":
            # A hint request always persists an agent hint even if the fake
            # gateway's default guidance reply was used.
            reply = reply.model_copy(update={"message_type": "hint"})

        state.last_agent_question = reply.message
        state.turn_index += 1
        learner_update = LearnerUpdate(
            level_score=turn.profile.level_score,
            assessment_count=turn.profile.assessment_count,
            current_level=turn.profile.current_level,
        )
        return AgentTurnOutput(
            reply=TutorReply.model_validate(reply),
            evaluation=None,
            performance=None,
            difficulty_used=state.difficulty,
            new_state=state,
            learner_update=learner_update,
            retrieved=[],
            rag_status="off",
        )

    def summarize(self, *args, **kwargs):
        raise NotImplementedError("TODO(phase-6): implement SocraticAgent.summarize")
