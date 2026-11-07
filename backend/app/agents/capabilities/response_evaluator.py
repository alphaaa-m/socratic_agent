"""Response evaluation (docs §16.6).

The evaluator builds the structured messages for the judge model and returns a
validated ``EvaluationResult``.  The gateway owns the retry policy for
transient network/provider errors.  The evaluator adds one application-level
retry for cases where the judge returns an invalid schema (FR-EVA-06).
"""

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.evaluation import EVALUATION_SYSTEM_PROMPT
from app.agents.schemas import EvaluationResult


class ResponseEvaluator:
    def __init__(self, gateway=None):
        self.gateway = gateway

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def evaluate(self, turn, state, chunks=None) -> EvaluationResult:
        """Build eval messages and call the judge model.

        The gateway owns the one retry for an invalid structured result.
        """
        messages = self._build_messages(turn, state, chunks)
        return self.gateway.evaluate(messages)

    # ------------------------------------------------------------------
    # Message construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_messages(turn, state, chunks=None) -> list:
        """Build the evaluation prompt messages (§16.6).

        The student message is wrapped in XML tags so that the judge model
        cannot confuse it with instructions.
        """
        references = []
        for index, chunk in enumerate(chunks or [], start=1):
            if isinstance(chunk, dict):
                title, content = chunk.get("title", "Untitled"), chunk.get("content", "")
            else:
                title, content = getattr(chunk, "title", "Untitled"), getattr(chunk, "content", "")
            references.append(f"[{index}] ({title}) {content}")
        reference_material = "\n".join(references) or "none"

        system_content = EVALUATION_SYSTEM_PROMPT.format(
            core_question=state.core_question or "(not yet set)",
            last_agent_question=state.last_agent_question or "(first turn)",
            reference_material=reference_material,
        )
        return [
            SystemMessage(content=system_content),
            HumanMessage(content=f"<student_message>{turn.student_message}</student_message>"),
        ]
