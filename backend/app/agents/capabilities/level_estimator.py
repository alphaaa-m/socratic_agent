"""Learner level estimation (docs §15.3).

The START_DIFFICULTY mapping is imported here from one canonical place so that
``session_service.py`` and other callers can share it without circular imports.
"""

from app.agents.schemas import LearnerUpdate, ProfileSnapshot

# ---------------------------------------------------------------------------
# Constants (§15.2 / §15.3)
# ---------------------------------------------------------------------------
START_DIFFICULTY: dict[str, int] = {"beginner": 2, "intermediate": 3, "advanced": 4}

ALPHA: float = 0.20          # EMA weight for the level score
MIN_ASSESSMENTS: int = 5     # minimum assessments before a level change is allowed


# ---------------------------------------------------------------------------
# Level weight helper
# ---------------------------------------------------------------------------
def _difficulty_weight(difficulty: int) -> float:
    """f(d) = 0.8 + 0.1 * (d − 1)   →   0.8 for d=1 … 1.2 for d=5."""
    return 0.8 + 0.1 * (difficulty - 1)


# ---------------------------------------------------------------------------
# Estimator
# ---------------------------------------------------------------------------
class LevelEstimator:
    """Stateless.  All computations return a fresh ``LearnerUpdate``."""

    def initial_difficulty(self, level: str) -> int:
        """Map beginner/intermediate/advanced to 2/3/4."""
        return START_DIFFICULTY[level]

    def update(
        self,
        profile: ProfileSnapshot,
        p: float,
        difficulty: int,
    ) -> LearnerUpdate:
        """EMA update with difficulty weighting and hysteresis (§15.3).

        Does not mutate the profile; returns a ``LearnerUpdate`` that the
        service layer persists in the same transaction.
        """
        f = _difficulty_weight(difficulty)
        x = min(1.0, p * f)
        score = round((1 - ALPHA) * profile.level_score + ALPHA * x, 3)
        count = profile.assessment_count + 1
        level = profile.current_level

        # Level changes require MIN_ASSESSMENTS assessments (hysteresis: the
        # demotion threshold is lower than the promotion threshold).
        if count >= MIN_ASSESSMENTS:
            if level == "beginner" and score >= 0.50:
                level = "intermediate"
            elif level == "intermediate" and score >= 0.78:
                level = "advanced"
            elif level == "intermediate" and score < 0.40:
                level = "beginner"
            elif level == "advanced" and score < 0.65:
                level = "intermediate"

        return LearnerUpdate(
            level_score=score,
            assessment_count=count,
            current_level=level,
        )
