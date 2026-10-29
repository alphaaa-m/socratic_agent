"""LLM gateway protocol plus deterministic and LangChain implementations."""

from typing import Protocol

from pydantic import ValidationError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.agents.schemas import (
    EvaluationResult,
    SessionSummary,
    SubjectRelevance,
    TutorReply,
)
from app.core.exceptions import LLMTimeoutError, LLMUnavailableError

_TIMEOUT_ERROR_NAMES = frozenset({"APITimeoutError", "ReadTimeout", "TimeoutException"})
_CONNECTION_ERROR_NAMES = frozenset(
    {"APIConnectionError", "ConnectError", "ConnectionError", "NetworkError"}
)
_RATE_LIMIT_ERROR_NAMES = frozenset({"RateLimitError", "TooManyRequestsError"})
_SERVER_ERROR_NAMES = frozenset({"InternalServerError", "ServiceUnavailableError"})


def _status_code(error: Exception) -> int | None:
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    return status if isinstance(status, int) else None


def _is_timeout(error: Exception) -> bool:
    return isinstance(error, TimeoutError) or error.__class__.__name__ in _TIMEOUT_ERROR_NAMES


def _is_retryable(error: Exception) -> bool:
    """Allow only transient network, timeout, 429, and provider-5xx failures."""
    status = _status_code(error)
    return (
        _is_timeout(error)
        or isinstance(error, ConnectionError)
        or error.__class__.__name__ in _CONNECTION_ERROR_NAMES
        or error.__class__.__name__ in _RATE_LIMIT_ERROR_NAMES
        or error.__class__.__name__ in _SERVER_ERROR_NAMES
        or status == 429
        or (status is not None and 500 <= status <= 599)
    )


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
def _invoke_with_retry(runnable, messages):
    return runnable.invoke(messages)


class LLMGateway(Protocol):
    def check_subject_relevance(self, messages: list) -> SubjectRelevance: ...
    def evaluate(self, messages: list) -> EvaluationResult: ...
    def generate_reply(self, messages: list) -> TutorReply: ...
    def summarize_session(self, messages: list) -> SessionSummary: ...
    def summarize_memory(self, messages: list) -> str: ...


class FakeGateway:
    """Deterministic gateway for tests and for phase 3."""

    def __init__(self):
        self.calls: list[tuple[str, list]] = []
        self.eval_queue: list[EvaluationResult] = []
        self.relevance_queue: list[SubjectRelevance] = []
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

    def check_subject_relevance(self, messages):
        self._enter("check_subject_relevance", messages)
        return self.relevance_queue.pop(0) if self.relevance_queue else SubjectRelevance(
            classification="relevant", reason=""
        )

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
    """Run structured LangChain calls with one centrally enforced retry policy."""

    def __init__(self, tutor_model, judge_model):
        self._reply = tutor_model.with_structured_output(TutorReply)
        self._relevance = judge_model.with_structured_output(SubjectRelevance)
        self._eval = judge_model.with_structured_output(EvaluationResult)
        self._summary = tutor_model.with_structured_output(SessionSummary)
        self._text = tutor_model

    @staticmethod
    def _call(runnable, messages):
        try:
            return _invoke_with_retry(runnable, messages)
        except Exception as error:
            if _is_timeout(error):
                raise LLMTimeoutError() from error
            raise LLMUnavailableError() from error

    @staticmethod
    def _structured(runnable, messages, schema):
        result = LangChainGateway._call(runnable, messages)
        try:
            return schema.model_validate(result)
        except ValidationError as error:
            raise LLMUnavailableError() from error

    def evaluate(self, messages) -> EvaluationResult:
        return self._structured(self._eval, messages, EvaluationResult)

    def check_subject_relevance(self, messages) -> SubjectRelevance:
        return self._structured(self._relevance, messages, SubjectRelevance)

    def generate_reply(self, messages) -> TutorReply:
        return self._structured(self._reply, messages, TutorReply)

    def summarize_session(self, messages) -> SessionSummary:
        return self._structured(self._summary, messages, SessionSummary)

    def summarize_memory(self, messages) -> str:
        result = self._call(self._text, messages)
        content = getattr(result, "content", result)
        if not isinstance(content, str):
            raise LLMUnavailableError()
        return content
