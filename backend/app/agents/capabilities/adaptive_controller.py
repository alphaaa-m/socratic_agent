"""Adaptive difficulty/hint controller -- Phase 5 (docs Sec 15.4)."""


class AdaptiveController:
    def raise_hint(self, state) -> None:
        raise NotImplementedError("TODO(phase-5): raise hint_level up to 3")

    def apply(self, state, evaluation) -> float:
        raise NotImplementedError("TODO(phase-5): streaks/difficulty/hint/resolved update")

    def select_mode(self, state) -> str:
        """Phase 4 deliberately selects only normal questions or hint rungs."""
        return "hint" if state.hint_level > 0 else "ask"
