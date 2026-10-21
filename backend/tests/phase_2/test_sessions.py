import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.models import LearnerProfile, LearningProgress, LearningSession, Subject, User
from app.services import session_service
from app.services.session_service import SessionService
from tests.phase_1.conftest import register
from tests.phase_2.conftest import authorization_for

pytestmark = pytest.mark.phase2


def make_subject(db, name="Session subject", active=True):
    subject = Subject(name=name, is_active=active)
    db.add(subject)
    db.flush()
    return subject


def test_starting_session_creates_state_and_updates_counters(client, db):
    account = register(client)
    subject = make_subject(db)
    response = client.post(
        "/api/v1/sessions",
        headers=authorization_for(client, account["email"]),
        json={"subject_id": str(subject.id)},
    )

    assert response.status_code == 201, response.text
    result = response.json()
    assert result["status"] == "active"
    assert result["ended_at"] is None
    session = db.get(LearningSession, uuid.UUID(result["id"]))
    profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == uuid.UUID(account["id"])))
    progress = db.scalar(
        select(LearningProgress).where(
            LearningProgress.user_id == uuid.UUID(account["id"]),
            LearningProgress.subject_id == subject.id,
        )
    )
    assert session.agent_state["difficulty"] == 2
    assert profile.total_sessions == 1
    assert progress.topics_attempted == 1


@pytest.mark.parametrize(("level", "difficulty"), [("beginner", 2), ("intermediate", 3), ("advanced", 4)])
def test_starting_difficulty_comes_from_the_learner_level(client, db, level, difficulty):
    account = register(client, email=f"{level}@example.com")
    profile = db.scalar(
        select(LearnerProfile).where(LearnerProfile.user_id == uuid.UUID(account["id"]))
    )
    profile.current_level = level
    subject = make_subject(db, name=f"{level} difficulty")
    db.commit()

    response = client.post(
        "/api/v1/sessions",
        headers=authorization_for(client, account["email"]),
        json={"subject_id": str(subject.id)},
    )
    assert response.status_code == 201
    session = db.get(LearningSession, uuid.UUID(response.json()["id"]))
    assert session.agent_state["difficulty"] == difficulty


def test_two_sessions_share_one_progress_row_and_increment_twice(client, db):
    account = register(client)
    subject = make_subject(db)
    headers = authorization_for(client, account["email"])

    assert client.post("/api/v1/sessions", headers=headers, json={"subject_id": str(subject.id)}).status_code == 201
    assert client.post("/api/v1/sessions", headers=headers, json={"subject_id": str(subject.id)}).status_code == 201

    rows = list(
        db.scalars(
            select(LearningProgress).where(
                LearningProgress.user_id == uuid.UUID(account["id"]),
                LearningProgress.subject_id == subject.id,
            )
        )
    )
    assert len(rows) == 1
    assert rows[0].topics_attempted == 2


def test_retired_or_missing_subject_cannot_start_a_session(client, db):
    account = register(client)
    retired = make_subject(db, name="Retired session subject", active=False)
    headers = authorization_for(client, account["email"])
    assert client.post("/api/v1/sessions", headers=headers, json={"subject_id": str(retired.id)}).status_code == 404
    assert client.post("/api/v1/sessions", headers=headers, json={"subject_id": str(uuid.uuid4())}).status_code == 404


def test_session_listing_is_owned_filtered_paged_and_newest_first(client, db):
    first = register(client, email="first@example.com")
    second = register(client, email="second@example.com")
    math = make_subject(db, "Math sessions")
    python = make_subject(db, "Python sessions")
    first_user = uuid.UUID(first["id"])
    second_user = uuid.UUID(second["id"])
    sessions = [
        LearningSession(
            user_id=first_user,
            subject_id=math.id,
            title="Old",
            agent_state={},
            started_at=datetime.now(UTC) - timedelta(minutes=2),
        ),
        LearningSession(
            user_id=first_user,
            subject_id=python.id,
            title="New",
            agent_state={},
            started_at=datetime.now(UTC) - timedelta(minutes=1),
        ),
        LearningSession(
            user_id=first_user,
            subject_id=python.id,
            title="Finished",
            status="abandoned",
            agent_state={},
            started_at=datetime.now(UTC) - timedelta(minutes=3),
            ended_at=datetime.now(UTC) - timedelta(minutes=2),
        ),
        LearningSession(
            user_id=second_user,
            subject_id=math.id,
            title="Private",
            agent_state={},
            started_at=datetime.now(UTC),
        ),
    ]
    db.add_all(sessions)
    db.flush()

    response = client.get(
        f"/api/v1/sessions?subject_id={math.id}&limit=1&offset=0",
        headers=authorization_for(client, first["email"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 1 and body["offset"] == 0
    assert [item["title"] for item in body["items"]] == ["Old"]

    all_sessions = client.get("/api/v1/sessions", headers=authorization_for(client, first["email"])).json()
    assert all(item["id"] != str(sessions[3].id) for item in all_sessions["items"])
    assert [item["title"] for item in all_sessions["items"]] == ["New", "Old", "Finished"]

    abandoned = client.get(
        "/api/v1/sessions?status=abandoned", headers=authorization_for(client, first["email"])
    )
    assert abandoned.status_code == 200
    assert abandoned.json()["total"] == 1
    assert [item["title"] for item in abandoned.json()["items"]] == ["Finished"]
    assert client.get("/api/v1/sessions?status=invalid", headers=authorization_for(client, first["email"])).status_code == 422


def test_session_detail_is_owner_only_and_does_not_include_messages(client, db):
    owner = register(client, email="owner@example.com")
    stranger = register(client, email="stranger@example.com")
    subject = make_subject(db)
    learning_session = LearningSession(
        user_id=uuid.UUID(owner["id"]), subject_id=subject.id, agent_state={"difficulty": 2}
    )
    db.add(learning_session)
    db.flush()

    own = client.get(
        f"/api/v1/sessions/{learning_session.id}", headers=authorization_for(client, owner["email"])
    )
    other = client.get(
        f"/api/v1/sessions/{learning_session.id}", headers=authorization_for(client, stranger["email"])
    )
    assert own.status_code == 200
    assert "messages" not in own.json()
    assert other.status_code == 404


def test_failed_progress_upsert_rolls_back_session_and_counter(client, db, monkeypatch):
    account = register(client)
    user = db.get(User, uuid.UUID(account["id"]))
    subject = make_subject(db)

    def fail_insert(*args, **kwargs):
        raise RuntimeError("progress insert failed")

    monkeypatch.setattr(session_service, "insert", fail_insert)
    with pytest.raises(RuntimeError, match="progress insert failed"):
        SessionService(db).create(user, subject.id)

    profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user.id))
    assert profile.total_sessions == 0
    assert db.scalar(select(func.count()).select_from(LearningSession).where(LearningSession.user_id == user.id)) == 0
