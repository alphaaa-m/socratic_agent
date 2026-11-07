"""Dialogue engine incl. answer-leak guard -- Phase 4 (docs Sec 14.6)."""

import logging

from langchain_core.messages import SystemMessage
from pydantic import ValidationError

from app.agents.schemas import TutorReply
from app.core.exceptions import LLMTimeoutError, LLMUnavailableError

logger = logging.getLogger(__name__)

FORBIDDEN_ANSWER_PHRASES = (
    "the answer is",
    "the correct answer is",
    "the final answer is",
    "the solution is",
    "the correct solution is",
    "the result is",
    "the final result is",
    "the answer to this question is",
)


class AnswerLeakGuard:
    """Small, predictable second line of defense for tutor reply text."""

    def check(self, message: str) -> list[str]:
        violations = []
        if "?" not in message:
            violations.append("reply must include a guiding question")
        if len(message.split()) > 120:
            violations.append("reply must contain 120 words or fewer")
        lowered = message.lower()
        matched = [phrase for phrase in FORBIDDEN_ANSWER_PHRASES if phrase in lowered]
        if matched:
            violations.append(f"reply contains forbidden answer phrase(s): {', '.join(matched)}")
        return violations


class DialogueEngine:
    def __init__(self, gateway=None, settings=None):
        self.gateway = gateway
        self.settings = settings
        self.guard = AnswerLeakGuard()

    def generate(self, messages, state, mode, chunks=None):
        """Generate once, then give the model one guarded correction chance."""
        reply = TutorReply.model_validate(self.gateway.generate_reply(messages))
        violations = self.guard.check(reply.message)
        if not violations:
            return self._reply_for_mode(reply, mode)

        logger.warning("tutor reply rejected by answer-leak guard", extra={"violations": violations})
        retry_messages = [
            *messages,
            SystemMessage(
                content=(
                    "Your prior proposed reply was rejected by the answer-leak guard for: "
                    f"{'; '.join(violations)}. Return one safe guiding question only."
                )
            ),
        ]
        retry = TutorReply.model_validate(self.gateway.generate_reply(retry_messages))
        retry_violations = self.guard.check(retry.message)
        if not retry_violations:
            return self._reply_for_mode(retry, mode)

        logger.warning(
            "tutor retry rejected by answer-leak guard", extra={"violations": retry_violations}
        )
        return self._template_question(state, mode)

    def closing_reply(self, turn, state, evaluation=None):
        """Generate a closing confirmation reply using mode ``close`` (§16.4).

        Uses the tutor model to produce a contextual closing message.  The
        answer-leak guard is NOT applied here because the close message does
        not need a question mark.  On any error, falls back to a template.
        """
        from app.agents.capabilities.hint_generator import HintGenerator
        from app.agents.capabilities.prompt_builder import PromptBuilder

        try:
            messages = PromptBuilder(HintGenerator()).tutor_messages(
                turn=turn,
                state=state,
                learner=turn.profile,
                chunks=[],
                mode="close",
                history=[],
                evaluation=evaluation,
            )
            raw = self.gateway.generate_reply(messages)
            reply = TutorReply.model_validate(raw)
            return reply.model_copy(update={"message_type": "guidance"})
        except (LLMTimeoutError, LLMUnavailableError, ValidationError, ValueError, TypeError):
            return self._closing_template(state)

    @staticmethod
    def _reply_for_mode(reply: TutorReply, mode: str) -> TutorReply:
        message_type = "hint" if mode in {"hint", "worked_analogy"} else "guidance"
        return reply.model_copy(update={"message_type": message_type})

    @staticmethod
    def _template_question(state, mode: str) -> TutorReply:
        concept = (state.target_concepts[0] if state.target_concepts else state.core_question) or "this topic"
        concept = " ".join(concept.replace("?", "").split()).rstrip(".!") or "this topic"
        return TutorReply(
            message=f"What do you already know about {concept}?",
            message_type="hint" if mode == "hint" else "guidance",
            target_concept=state.target_concepts[0] if state.target_concepts else None,
        )

    @staticmethod
    def _closing_template(state) -> TutorReply:
        """Safe fallback closing message."""
        return TutorReply(
            message=(
                "You've reached the correct reasoning. Well done! "
                "You can end the session now to see your summary."
            ),
            message_type="guidance",
        )
