"""Adaptive difficulty/hint controller (docs §15.4).

All constants are centralised here so that tests and the level estimator can
import them from one place.
"""

from app.agents.schemas import AgentState, EvaluationResult

# ---------------------------------------------------------------------------
# Constants (§15.2)
# ---------------------------------------------------------------------------
W_CORRECT: float = 0.55
W_REASON: float = 0.45

HIGH: float = 0.75   # p >= HIGH → high-performance turn
LOW: float = 0.40    # p < LOW  → low-performance turn

RESOLVE_C: float = 0.85  # minimum correctness_score for resolution
RESOLVE_R: float = 0.75  # minimum reasoning_score for resolution

STREAK_N: int = 2        # consecutive turns needed to change difficulty


# ---------------------------------------------------------------------------
# Standalone performance helper (§15.1)
# ---------------------------------------------------------------------------
def performance(e: EvaluationResult) -> float:
    """Return the performance score p = 0.55·c + 0.45·r."""
    return W_CORRECT * e.correctness_score + W_REASON * e.reasoning_score


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------
class AdaptiveController:
    """Stateless adaptive controller.  All mutations are on the *state* copy
    that the agent already holds; the controller does not own any state."""

    def raise_hint(self, s: AgentState) -> None:
        """Raise hint_level by one (capped at 3) and increment hints_used."""
        if s.hint_level < 3:
            s.hint_level += 1
            s.hints_used += 1

    def apply(self, s: AgentState, e: EvaluationResult) -> float:
        """Apply one assessment to the session state.

        Returns the computed performance score p.  The state is mutated
        in-place (the agent already works on a deep copy).
        """
        p = performance(e)
        s.perf_history.append(round(p, 3))

        # --- streak / stuck accounting ---
        if p >= HIGH:
            s.high_streak += 1
            s.low_streak = 0
            s.stuck_turns = 0
            if s.hint_level > 0:
                s.hint_level -= 1
        elif p < LOW:
            s.low_streak += 1
            s.high_streak = 0
            s.stuck_turns += 1
        else:
            # neutral turn resets both streaks
            s.high_streak = 0
            s.low_streak = 0

        # --- difficulty changes ---
        if s.high_streak >= STREAK_N:
            s.difficulty = min(5, s.difficulty + 1)
            s.high_streak = 0
        if s.low_streak >= STREAK_N:
            s.difficulty = max(1, s.difficulty - 1)
            s.low_streak = 0
            self.raise_hint(s)

        # --- explicit hint request ---
        if e.requests_hint:
            self.raise_hint(s)

        # --- misconception tracking ---
        if e.misconception:
            s.misconceptions[e.misconception] = (
                s.misconceptions.get(e.misconception, 0) + 1
            )

        # --- demonstrated concepts ---
        for concept in e.demonstrated_concepts:
            if concept not in s.demonstrated_concepts:
                s.demonstrated_concepts.append(concept)

        # --- goal resolution (§15.7) ---
        s.resolved = (
            e.addresses_core_question
            and e.correctness_score >= RESOLVE_C
            and e.reasoning_score >= RESOLVE_R
        )

        return p

    def select_mode(self, s: AgentState) -> str:
        """Return the dialogue mode: ``close``, ``worked_analogy``, ``hint`` or ``ask``."""
        if s.resolved:
            return "close"
        if s.stuck_turns >= 3 and s.hint_level == 3:
            return "worked_analogy"
        return "hint" if s.hint_level > 0 else "ask"
