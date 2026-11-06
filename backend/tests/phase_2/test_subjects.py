import uuid

import pytest
from sqlalchemy import select

from app.models import LearningSession, Subject, User
from tests.phase_1.conftest import register
from tests.phase_2.conftest import authorization_for

pytestmark = pytest.mark.phase2


def make_admin(client, db, email="admin@example.com"):
    admin = register(client, email=email, name="Admin User")
    user = db.get(User, uuid.UUID(admin["id"]))
    user.role = "admin"
    db.commit()
    return admin, authorization_for(client, email)


def test_subject_listing_defaults_to_active_and_can_include_retired(client, db, auth):
    active = Subject(name="Active geography", description="Maps")
    retired = Subject(name="Retired geography", description="Old maps", is_active=False)
    db.add_all([active, retired])
    db.flush()

    active_only = client.get("/api/v1/subjects", headers=auth)
    all_subjects = client.get("/api/v1/subjects?active_only=false", headers=auth)

    assert active_only.status_code == 200
    assert active.name in [item["name"] for item in active_only.json()]
    assert retired.name not in [item["name"] for item in active_only.json()]
    assert retired.name in [item["name"] for item in all_subjects.json()]
    assert [item["name"] for item in all_subjects.json()] == sorted(
        (item["name"] for item in all_subjects.json()), key=str.casefold
    )


def test_six_default_subjects_are_present_and_seeding_is_idempotent(db):
    from app.services.subject_seed import DEFAULT_SUBJECTS, seed_default_subjects

    assert seed_default_subjects(db) >= 0
    db.commit()
    assert seed_default_subjects(db) == 0
    names = set(db.scalars(select(Subject.name).where(Subject.owner_id.is_(None))))
    assert {name for name, _ in DEFAULT_SUBJECTS} <= names


def test_subject_detail_missing_and_student_can_create_but_cannot_manage_defaults(client, auth):
    assert client.get(f"/api/v1/subjects/{uuid.uuid4()}", headers=auth).status_code == 404
    custom = client.post("/api/v1/subjects", headers=auth, json={"name": "My topic"})
    assert custom.status_code == 201
    assert custom.json()["is_default"] is False
    assert client.post("/api/v1/subjects", headers=auth, json={"name": "Python"}).status_code == 201


def test_custom_subjects_are_private_and_duplicate_names_are_per_user(client, db, auth):
    owner = register(client, email="owner@example.com")
    owner_auth = authorization_for(client, owner["email"])
    other = register(client, email="other@example.com")
    other_auth = authorization_for(client, other["email"])
    created = client.post("/api/v1/subjects", headers=owner_auth, json={"name": "Astronomy"})
    subject_id = created.json()["id"]

    assert client.get("/api/v1/subjects", headers=owner_auth).json()
    assert subject_id not in [item["id"] for item in client.get("/api/v1/subjects", headers=other_auth).json()]
    assert client.get(f"/api/v1/subjects/{subject_id}", headers=other_auth).status_code == 404
    assert client.patch(f"/api/v1/subjects/{subject_id}", headers=other_auth, json={"name": "Changed"}).status_code == 404
    assert client.delete(f"/api/v1/subjects/{subject_id}", headers=other_auth).status_code == 404
    assert client.post("/api/v1/subjects", headers=owner_auth, json={"name": "astronomy"}).status_code == 409
    assert client.post("/api/v1/subjects", headers=other_auth, json={"name": "Astronomy"}).status_code == 201


def test_admin_can_create_update_and_retire_subjects_and_duplicate_is_conflict(client, db):
    _, admin_auth = make_admin(client, db)
    created = client.post(
        "/api/v1/subjects",
        headers=admin_auth,
        json={"name": "Chemistry", "description": "Atoms"},
    )
    assert created.status_code == 201, created.text
    subject_id = created.json()["id"]

    duplicate = client.post("/api/v1/subjects", headers=admin_auth, json={"name": "Chemistry"})
    updated = client.patch(
        f"/api/v1/subjects/{subject_id}",
        headers=admin_auth,
        json={"description": None, "is_active": False},
    )

    assert duplicate.status_code == 409
    assert updated.status_code == 200
    assert updated.json()["description"] is None
    assert updated.json()["is_active"] is False


def test_admin_can_update_default_but_student_cannot(client, db, auth):
    default = Subject(name="Shared Default")
    db.add(default)
    db.flush()
    assert client.patch(
        f"/api/v1/subjects/{default.id}", headers=auth, json={"name": "Changed"}
    ).status_code == 403
    _, admin_auth = make_admin(client, db)
    assert client.patch(
        f"/api/v1/subjects/{default.id}", headers=admin_auth, json={"description": "Updated"}
    ).status_code == 200


def test_admin_cannot_delete_subject_with_history_but_can_delete_empty_subject(client, db):
    _, admin_auth = make_admin(client, db)
    empty = Subject(name="Empty subject")
    used = Subject(name="Used subject")
    db.add_all([empty, used])
    db.flush()
    db.add(
        LearningSession(
            user_id=uuid.UUID(register(client, email="learner@example.com")["id"]),
            subject_id=used.id,
            agent_state={},
        )
    )
    db.flush()

    blocked = client.delete(f"/api/v1/subjects/{used.id}", headers=admin_auth)
    deleted = client.delete(f"/api/v1/subjects/{empty.id}", headers=admin_auth)

    assert blocked.status_code == 409
    assert "Retire" in blocked.json()["error"]["message"]
    assert deleted.status_code == 204
    assert db.scalar(select(Subject).where(Subject.id == empty.id)) is None
