"""Learner level estimation -- Phase 5 (docs Sec 15.3)."""


class LevelEstimator:
    def initial_difficulty(self, level: str) -> int:
        raise NotImplementedError("TODO(phase-5): map beginner/intermediate/advanced to 2/3/4")

    def update(self, profile, p: float, difficulty: int):
        raise NotImplementedError("TODO(phase-5): EMA level_score update with hysteresis")
