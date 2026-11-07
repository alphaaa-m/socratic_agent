import pytest

from app.agents.capabilities.adaptive_controller import AdaptiveController, performance
from app.agents.capabilities.level_estimator import LevelEstimator
from app.agents.schemas import AgentState, EvaluationResult, ProfileSnapshot


def evaluation(c, r, **kwargs):
    return EvaluationResult(
        correctness_score=c,
        reasoning_score=r,
        confidence_score=kwargs.get("confidence", 0.5),
        feedback="Keep going.",
        addresses_core_question=kwargs.get("addresses", False),
        requests_hint=kwargs.get("hint", False),
        misconception=kwargs.get("misconception"),
        demonstrated_concepts=kwargs.get("concepts", []),
    )


def test_performance_boundaries_and_streak_transitions():
    controller = AdaptiveController()
    state = AgentState(difficulty=3)
    assert performance(evaluation(1, 4 / 9)) == pytest.approx(0.75)
    assert controller.apply(state, evaluation(1, 4 / 9)) == pytest.approx(0.75)
    assert state.high_streak == 1
    controller.apply(state, evaluation(0.4, 0.4))
    assert state.difficulty == 3
    assert state.high_streak == state.low_streak == 0
    controller.apply(state, evaluation(0, 0))
    controller.apply(state, evaluation(0, 0))
    assert state.difficulty == 2
    assert state.hint_level == 1


def test_high_turn_hint_request_and_hint_decay_order():
    controller = AdaptiveController()
    state = AgentState(hint_level=2, hints_used=2)
    controller.apply(state, evaluation(1, 1, hint=True))
    assert state.hint_level == 2  # high turn lowers one rung, request raises one
    assert state.hints_used == 3


def test_difficulty_and_hint_caps_and_resolution_policy():
    controller = AdaptiveController()
    state = AgentState(difficulty=5, hint_level=3)
    controller.apply(state, evaluation(1, 1))
    controller.apply(state, evaluation(1, 1, addresses=True))
    assert state.difficulty == 5
    assert state.resolved is True
    assert controller.select_mode(state) == "close"
    partial = AgentState()
    controller.apply(partial, evaluation(1, 1, addresses=False))
    assert not partial.resolved


def test_low_streak_stuck_policy_and_misconception_tracking():
    controller = AdaptiveController()
    state = AgentState(hint_level=1)
    for i in range(3):
        controller.apply(state, evaluation(0, 0, misconception="wrong rule", concepts=[f"c{i}"]))
        if i < 2:
            controller.raise_hint(state)
    assert state.stuck_turns == 3
    assert state.hint_level == 3
    assert controller.select_mode(state) == "worked_analogy"
    assert state.misconceptions["wrong rule"] == 3


def test_level_estimator_ema_and_minimum_assessments():
    estimator = LevelEstimator()
    profile = ProfileSnapshot(current_level="beginner", level_score=0.3, assessment_count=0)
    first = estimator.update(profile, 0.355, 2)
    assert first.level_score == 0.304
    assert first.assessment_count == 1
    profile = profile.model_copy(update={"level_score": first.level_score, "assessment_count": 1})
    second = estimator.update(profile, 0.855, 2)
    assert second.level_score == 0.397


def test_level_estimator_third_example_update():
    update = LevelEstimator().update(
        ProfileSnapshot(current_level="beginner", level_score=0.397, assessment_count=2),
        0.9275,
        2,
    )
    assert update.level_score == 0.485


def test_misconception_normalization_empty_truncation_and_punctuation():
    from app.agents.capabilities.misconception_detector import MisconceptionDetector

    detector = MisconceptionDetector()
    assert detector.normalize(evaluation(0, 0, misconception="  Rounded DECIMAL! ")).misconception == "rounded decimal"
    assert detector.normalize(evaluation(0, 0, misconception="  !!! ")).misconception is None
    assert len(detector.normalize(evaluation(0, 0, misconception="X" * 140)).misconception) == 120

