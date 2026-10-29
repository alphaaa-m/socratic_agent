"""Hint generation -- Phase 4 (docs Sec 15.4 hint ladder)."""

from app.agents.prompts import ASK_INSTRUCTION, HINT_INSTRUCTIONS


class HintGenerator:
    def instruction(self, hint_level: int) -> str:
        """Return the prompt instruction for the current hint rung.

        State validation keeps values between zero and three.  Treating zero as
        the normal asking mode also makes this helper safe for direct use in
        prompt-layer tests.
        """
        if hint_level <= 0:
            return ASK_INSTRUCTION
        return HINT_INSTRUCTIONS[min(hint_level, 3)]
