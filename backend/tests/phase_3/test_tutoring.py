from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.exceptions import TurnConflictError
from app.models import LearningSession, Message, Subject, User
from app.services.tutoring_service import TutoringService
from tests.phase_1.conftest import register
from tests.phase_2.conftest import authorization_for

pytestmark = pytest.mark.phase3


def create_session(client, db, email="student@example.com"):
    account = register(client, email=email)
    subject = Subject(name=f"Subject for {email}", description="A test subject")
    db.add(subject)
    db.flush()
    headers = authorization_for(client, account["email"])
    response = client.post("/api/v1/sessions", headers=headers, json={"subject_id": str(subject.id)})
    assert response.status_code == 201, response.text
    return account, headers, subject, response.json()["id"]


def test_first_and_second_messages_save_a_complete_turn_and_title(client, db):
    _, headers, _, session_id = create_session(client, db)
    question = "Why does a decimal calculation sometimes differ from the expected result?"

    first = client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers, json={"content": question})
    second = client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers, json={"content": "I think binary fractions are involved."})

    assert first.status_code == 201, first.text
    body = first.json()
    assert body["student_message"]["message_type"] == "question"
    assert body["agent_message"]["message_type"] == "guidance"
    assert body["assessment"] is None
    assert body["session_state"]["rag_status"] == "off"
    assert body["session_state"]["difficulty"] == 2
    assert second.status_code == 201, second.text
    assert second.json()["student_message"]["message_type"] == "response"

    session = db.get(LearningSession, session_id)
    assert session.title == question[:60]
    assert session.agent_state["turn_index"] == 2
    assert db.scalar(select(func.count()).select_from(Message).where(Message.session_id == session.id)) == 4


def test_fake_gateway_uses_its_canned_reply_for_each_unqueued_turn(client, db):
    _, headers, _, session_id = create_session(client, db, "canned-reply@example.com")

    first = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        headers=headers,
        json={"content": "What is a binary fraction?"},
    )
    second = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        headers=headers,
        json={"content": "I think it has a denominator that is a power of two."},
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["agent_message"]["content"] == "What do you already know about this topic?"
    assert second.json()["agent_message"]["content"] == "What do you already know about this topic?"


def test_list_messages_is_owned_ordered_and_paginated(client, db):
    owner, owner_headers, _subject, session_id = create_session(client, db, "owner-list@example.com")
    stranger = register(client, email="stranger-list@example.com")
    learning_session = db.get(LearningSession, session_id)
    start = datetime.now(UTC) - timedelta(minutes=3)
    db.add_all(
        [
            Message(session_id=learning_session.id, sender="student", message_type="question", content="First", created_at=start),
            Message(session_id=learning_session.id, sender="agent", message_type="guidance", content="Second", created_at=start + timedelta(minutes=1)),
            Message(session_id=learning_session.id, sender="student", message_type="response", content="Third", created_at=start + timedelta(minutes=2)),
        ]
    )
    db.flush()

    listed = client.get(f"/api/v1/sessions/{session_id}/messages?limit=2&offset=1", headers=owner_headers)
    private = client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=authorization_for(client, stranger["email"]),
    )

    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 3
    assert listed.json()["limit"] == 2 and listed.json()["offset"] == 1
    assert [item["content"] for item in listed.json()["items"]] == ["Second", "Third"]
    assert private.status_code == 404
    # Keep the owner variable deliberate: this test must use the owner session.
    assert owner["email"] == "owner-list@example.com"


def test_messages_are_owner_only_and_active_sessions_are_required(client, db):
    _, owner_headers, _, session_id = create_session(client, db, "owner-send@example.com")
    stranger = register(client, email="stranger-send@example.com")
    stranger_headers = authorization_for(client, stranger["email"])

    assert client.post(
        f"/api/v1/sessions/{session_id}/messages", headers=stranger_headers, json={"content": "Let me in"}
    ).status_code == 404

    session = db.get(LearningSession, session_id)
    session.status = "abandoned"
    session.ended_at = datetime.now(UTC)
    db.commit()
    inactive = client.post(
        f"/api/v1/sessions/{session_id}/messages", headers=owner_headers, json={"content": "Still there?"}
    )
    assert inactive.status_code == 409
    assert inactive.json()["error"]["code"] == "SESSION_NOT_ACTIVE"


@pytest.mark.parametrize("content", ["", "   ", "x" * 4001])
def test_message_validation(client, db, content):
    _, headers, _, session_id = create_session(client, db, f"validation-{len(content)}@example.com")
    response = client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers, json={"content": content})
    assert response.status_code == 422


def test_gateway_failure_saves_no_partial_turn(client, db, fake_gateway):
    _, headers, _, session_id = create_session(client, db, "atomicity@example.com")
    fake_gateway.fail_next("generate_reply")

    response = client.post(
        f"/api/v1/sessions/{session_id}/messages", headers=headers, json={"content": "Will this save?"}
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "LLM_UNAVAILABLE"
    assert db.scalar(select(func.count()).select_from(Message).where(Message.session_id == session_id)) == 0
    assert db.get(LearningSession, session_id).agent_state["turn_index"] == 0


def test_turn_conflict_rolls_back_every_pending_write(client, db, monkeypatch):
    account, _, _, session_id = create_session(client, db, "conflict@example.com")
    service = TutoringService(db, client.app.state.agent)
    original_lock = service._lock_active_session

    def conflicting_lock(*args):
        session = original_lock(*args)
        state = dict(session.agent_state)
        state["turn_index"] = state.get("turn_index", 0) + 1
        session.agent_state = state
        return session

    monkeypatch.setattr(service, "_lock_active_session", conflicting_lock)
    with pytest.raises(TurnConflictError):
        service.handle_student_message(db.get(User, account["id"]), session_id, "Race condition?")
    assert db.scalar(select(func.count()).select_from(Message).where(Message.session_id == session_id)) == 0


def test_hint_only_saves_agent_message_and_caps_hint_level(client, db):
    _, headers, _, session_id = create_session(client, db, "hints@example.com")

    responses = [client.post(f"/api/v1/sessions/{session_id}/hints", headers=headers) for _ in range(4)]

    assert all(response.status_code == 201 for response in responses)
    assert all(response.json()["agent_message"]["message_type"] == "hint" for response in responses)
    final = responses[-1].json()["session_state"]
    assert final["hint_level"] == 3
    assert db.get(LearningSession, session_id).agent_state["hints_used"] == 4
    messages = list(db.scalars(select(Message).where(Message.session_id == session_id)))
    assert len(messages) == 4
    assert {message.sender for message in messages} == {"agent"}


def test_post_endpoints_rate_limit_authenticated_user(client, db):
    _, headers, _, session_id = create_session(client, db, "rate-limit@example.com")
    responses = [
        client.post(f"/api/v1/sessions/{session_id}/messages", headers=headers, json={"content": f"Turn {index}"})
        for index in range(21)
    ]
    assert all(response.status_code == 201 for response in responses[:20])
    assert responses[-1].status_code == 429
    assert responses[-1].json()["error"]["code"] == "RATE_LIMITED"


def test_agent_runs_after_the_read_transaction_has_closed(client, db):
    account, _, _, session_id = create_session(client, db, "connection@example.com")
    real_agent = client.app.state.agent

    class TransactionSpy:
        def __init__(self):
            self.seen_open_transaction = None

        def handle_turn(self, turn):
            self.seen_open_transaction = db.in_transaction()
            return real_agent.handle_turn(turn)

    spy = TransactionSpy()
    result = TutoringService(db, spy).handle_student_message(
        db.get(User, account["id"]), session_id, "Is this connection released?"
    )
    assert result.student_message.message_type == "question"
    assert spy.seen_open_transaction is False
