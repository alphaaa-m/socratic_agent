"""LLM gateway protocol + FakeGateway (complete). LangChainGateway is Phase 4."""

from typing import Protocol

from app.agents.schemas import EvaluationResult, SessionSummary, TutorReply
from app.core.exceptions import LLMUnavailableError


class LLMGateway(Protocol):
    def evaluate(self, messages: list) -> EvaluationResult: ...
    def generate_reply(self, messages: list) -> TutorReply: ...
    def summarize_session(self, messages: list) -> SessionSummary: ...
    def summarize_memory(self, messages: list) -> str: ...


class FakeGateway:
    """Deterministic gateway for tests and for phase 3."""

    def __init__(self):
        self.calls: list[tuple[str, list]] = []
        self.eval_queue: list[EvaluationResult] = []
        self.reply_queue: list[TutorReply] = []
        self._fail: set[str] = set()

    def fail_next(self, method: str) -> None:
        self._fail.add(method)

    def _enter(self, name, messages):
        self.calls.append((name, messages))
        if name in self._fail:
            self._fail.discard(name)
            raise LLMUnavailableError()

    def evaluate(self, messages):
        self._enter("evaluate", messages)
        return self.eval_queue.pop(0) if self.eval_queue else EvaluationResult(
            correctness_score=0.5, reasoning_score=0.5, confidence_score=0.5,
            feedback="Good effort.", addresses_core_question=False)

    def generate_reply(self, messages):
        self._enter("generate_reply", messages)
        return self.reply_queue.pop(0) if self.reply_queue else TutorReply(
            message="What do you already know about this topic?", message_type="guidance")

    def summarize_session(self, messages):
        self._enter("summarize_session", messages)
        return SessionSummary(outcome="partial", overview="Fake summary.", key_concepts=[], strengths=[],
                              misconceptions_addressed=[], areas_to_review=[], next_steps=[])

    def summarize_memory(self, messages):
        self._enter("summarize_memory", messages)
        return "Fake memory summary."


class LangChainGateway:
    """Phase 4: wraps LangChain chat models with structured output (docs Sec 16.7)."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("TODO(phase-4): build LangChainGateway with tutor/judge models")

    def evaluate(self, messages):
        raise NotImplementedError("TODO(phase-4): structured EvaluationResult via judge model")

    def generate_reply(self, messages):
        raise NotImplementedError("TODO(phase-4): structured TutorReply via tutor model")

    def summarize_session(self, messages):
        raise NotImplementedError("TODO(phase-4): structured SessionSummary via tutor model")

    def summarize_memory(self, messages):
        raise NotImplementedError("TODO(phase-4): rolling memory summary via tutor model")
