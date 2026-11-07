from sqlalchemy import func, select

from app.agents.schemas import EvaluationResult
from app.models import (
    LearnerAssessment,
    LearnerProfile,
    LearningSession,
    Message,
    Subject,
)
from tests.phase_1.conftest import register
from tests.phase_2.conftest import authorization_for


def create(client, db, email):
    user_data = register(client, email=email)
    subject = Subject(name=f"Subject {email}", description="Tests")
    db.add(subject)
    db.flush()
    headers = authorization_for(client, email)
    response = client.post("/api/v1/sessions", headers=headers, json={"subject_id": str(subject.id)})
    assert response.status_code == 201, response.text
    return user_data, headers, response.json()["id"]


def result(c, r, k, feedback, *, addresses=False, misconception=None, hint=False, concepts=None):
    return EvaluationResult(
        correctness_score=c, reasoning_score=r, confidence_score=k,
        feedback=feedback, addresses_core_question=addresses,
        misconception=misconception, requests_hint=hint,
        demonstrated_concepts=concepts or [],
    )


def test_example_session_exact_values_persistence_and_assessment_ownership(client, db, fake_gateway):
    _, headers, session_id = create(client, db, "phase5-example@example.com")
    assert client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers,
                       json={"content": "Why does 0.1 + 0.2 == 0.3 return False in Python?"}).status_code == 201
    fake_gateway.eval_queue.extend([
        result(.4, .3, .4, "Good try.", misconception=" Treats a rounded decimal as an exact value! ", hint=True),
        result(.9, .8, .8, "You identified a useful base 10 pattern."),
        result(.95, .9, .9, "You connected the idea to binary storage.", addresses=True,
               concepts=["finite and repeating expansions"]),
    ])
    expected_p = [.355, .855, .9275]
    expected_s = [.304, .397, .485]
    states = []
    for index in range(3):
        response = client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers,
                               json={"content": f"answer {index}"})
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["assessment"]["feedback"]
        assert body["session_state"]["resolved"] is (index == 2)
        states.append(body["session_state"])
        # Stored performance is rounded to the assessment precision (3 places).
        session = db.get(LearningSession, session_id)
        assert session.agent_state["perf_history"][-1] == round(expected_p[index], 3)
        profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == session.user_id))
        assert profile.level_score == expected_s[index]
    assert states[0]["hint_level"] == 1
    assert states[1]["hint_level"] == 0
    assert states[2]["resolved"] is True
    assert len(fake_gateway.eval_queue) == 0
    assessments = list(db.scalars(select(LearnerAssessment).where(LearnerAssessment.session_id == session_id)))
    assert len(assessments) == 3
    assert assessments[0].difficulty_level == 2
    assert assessments[2].resolves_goal is True
    assert assessments[0].misconception == "treats a rounded decimal as an exact value"
    assert client.get(f"/api/v1/sessions/{session_id}/assessments", headers=headers).status_code == 200
    own_assessment = client.get(f"/api/v1/assessments/{assessments[0].id}", headers=headers)
    assert own_assessment.status_code == 200
    stranger = register(client, email="phase5-stranger@example.com")
    foreign_headers = authorization_for(client, stranger["email"])
    assert client.get(f"/api/v1/assessments/{assessments[0].id}", headers=foreign_headers).status_code == 404
    assert client.get(f"/api/v1/sessions/{session_id}/assessments", headers=foreign_headers).status_code == 404


def test_evaluation_failure_rolls_back_all_turn_writes(client, db, fake_gateway):
    _user, headers, session_id = create(client, db, "phase5-rollback@example.com")
    client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers,
                json={"content": "What is the question?"})
    fake_gateway.fail_next("evaluate")
    response = client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers,
                           json={"content": "An answer."})
    assert response.status_code == 503
    assert db.scalar(select(func.count()).select_from(LearnerAssessment).where(
        LearnerAssessment.session_id == session_id)) == 0
    assert db.scalar(select(func.count()).select_from(Message).where(
        Message.session_id == session_id)) == 2
    assert db.get(LearningSession, session_id).agent_state["turn_index"] == 1


def test_resolved_session_does_not_accept_more_messages(client, db, fake_gateway):
    _, headers, session_id = create(client, db, "phase5-resolved@example.com")
    client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers,
                json={"content": "Why?"})
    fake_gateway.eval_queue.append(result(.9, .8, .8, "Well reasoned.", addresses=True))
    closing = client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers,
                          json={"content": "Complete answer"})
    assert closing.status_code == 201
    assert closing.json()["session_state"]["resolved"] is True
    assert len(fake_gateway.eval_queue) == 0
    rejected = client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers,
                           json={"content": "More"})
    assert rejected.status_code == 409
