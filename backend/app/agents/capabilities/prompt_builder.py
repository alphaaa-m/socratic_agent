"""Prompt construction -- Phase 4 (docs Sec 16)."""

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import (
    MEMORY_TEMPLATE,
    MODE_INSTRUCTIONS,
    NO_REFERENCE_MATERIAL,
    OUTPUT_REQUIREMENTS,
    REFERENCE_MATERIAL_TEMPLATE,
    STUDENT_CONTEXT_TEMPLATE,
    SUBJECT_CONTEXT_TEMPLATE,
    SYSTEM_PROMPT,
)


class PromptBuilder:
    def __init__(self, hints=None):
        self.hints = hints

    def tutor_messages(self, turn, state, learner, chunks, mode, history):
        """Build the fixed nine-layer prompt without trusting student content."""
        return [
            self._system_layer(),
            self._student_context_layer(turn, state, learner),
            self._subject_context_layer(turn, state),
            self._memory_layer(state),
            self._reference_material_layer(chunks),
            self._mode_layer(state, mode),
            *history[-10:],
            self._student_message_layer(turn),
            self._output_layer(),
        ]

    @staticmethod
    def _system_layer() -> SystemMessage:
        return SystemMessage(content=SYSTEM_PROMPT)

    @staticmethod
    def _student_context_layer(turn, state, learner) -> SystemMessage:
        profile = turn.profile
        preferences = getattr(profile, "learning_preferences", {}) or "none"
        recurring = [
            label for label, count in state.misconceptions.items() if count >= 2
        ]
        return SystemMessage(
            content=STUDENT_CONTEXT_TEMPLATE.format(
                current_level=getattr(learner, "current_level", profile.current_level),
                level_score=getattr(learner, "level_score", profile.level_score),
                difficulty=state.difficulty,
                hint_level=state.hint_level,
                calibration="not yet assessed",
                recurring_misconceptions=", ".join(recurring) or "none",
                learning_preferences=preferences,
            )
        )

    @staticmethod
    def _subject_context_layer(turn, state) -> SystemMessage:
        return SystemMessage(
            content=SUBJECT_CONTEXT_TEMPLATE.format(
                subject_name=turn.subject_name,
                subject_description=turn.subject_description or "(no description provided)",
                core_question=state.core_question or "(not yet set)",
                target_concepts=", ".join(state.target_concepts) or "not yet known",
            )
        )

    @staticmethod
    def _memory_layer(state) -> SystemMessage:
        return SystemMessage(
            content=MEMORY_TEMPLATE.format(memory_summary=state.memory_summary or "(no summary yet)")
        )

    @staticmethod
    def _reference_material_layer(chunks) -> SystemMessage:
        references = []
        for index, chunk in enumerate(chunks or [], start=1):
            if isinstance(chunk, dict):
                title = chunk.get("title", "Untitled")
                content = chunk.get("content", "")
            else:
                title = getattr(chunk, "title", "Untitled")
                content = getattr(chunk, "content", "")
            references.append(f"[{index}] ({title}) {content}")
        material = "\n".join(references) if references else NO_REFERENCE_MATERIAL
        return SystemMessage(content=REFERENCE_MATERIAL_TEMPLATE.format(reference_material=material))

    def _mode_layer(self, state, mode) -> SystemMessage:
        if mode == "hint":
            instruction = self.hints.instruction(state.hint_level)
        elif mode == "ask":
            instruction = self.hints.instruction(0).format(difficulty=state.difficulty)
        else:
            instruction = MODE_INSTRUCTIONS[mode]
        return SystemMessage(content=f"MODE: {instruction}")

    @staticmethod
    def _student_message_layer(turn) -> HumanMessage:
        return HumanMessage(content=f"<student_message>{turn.student_message}</student_message>")

    @staticmethod
    def _output_layer() -> SystemMessage:
        return SystemMessage(content=OUTPUT_REQUIREMENTS)
