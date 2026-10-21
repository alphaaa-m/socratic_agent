import uuid

import pytest

from app.models import User
from tests.phase_1.conftest import register
from tests.phase_2.conftest import authorization_for

pytestmark = pytest.mark.phase2


def make_admin(client, db):
    created = register(client, email="admin@example.com", name="Admin User")
    admin = db.get(User, uuid.UUID(created["id"]))
    admin.role = "admin"
    db.commit()
    return created, authorization_for(client, created["email"])


def test_students_are_forbidden_from_admin_user_endpoints(client, auth):
    assert client.get("/api/v1/users", headers=auth).status_code == 403
    assert client.patch(f"/api/v1/users/{uuid.uuid4()}", headers=auth, json={"role": "admin"}).status_code == 403


def test_admin_user_search_role_filter_pagination_and_self_protection(client, db):
    admin, admin_auth = make_admin(client, db)
    first = register(client, email="amy@example.com", name="Amy Student")
    register(client, email="bea@example.com", name="Bea Student")

    filtered = client.get("/api/v1/users?role=student&q=amy&limit=1&offset=0", headers=admin_auth)
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["email"] == "amy@example.com"

    promoted = client.patch(f"/api/v1/users/{first['id']}", headers=admin_auth, json={"role": "admin"})
    demote_self = client.patch(f"/api/v1/users/{admin['id']}", headers=admin_auth, json={"role": "student"})
    disable_self = client.patch(f"/api/v1/users/{admin['id']}", headers=admin_auth, json={"is_active": False})
    assert promoted.status_code == 200 and promoted.json()["role"] == "admin"
    assert demote_self.status_code == 400
    assert disable_self.status_code == 400
