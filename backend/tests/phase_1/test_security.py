"""Cross-cutting security rules from Sec 26 (FR-JWT-05, FR-ACC-03)."""

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.auth.jwt import ACCESS, create_token
from app.models import User

pytestmark = pytest.mark.phase1


def test_unauthenticated_requests_are_rejected_not_501(client):
    """Phase 1 turns the old 501s into real 401s."""
    for path in ("/api/v1/users/me", "/api/v1/subjects", "/api/v1/sessions"):
        response = client.get(path)
        assert response.status_code == 401, f"{path}: {response.text}"
        assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_admin_endpoint_rejects_a_student(client, auth):
    response = client.get("/api/v1/users", headers=auth)

    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_a_token_claiming_admin_does_not_make_you_admin(client, account):
    """FR-JWT-05: the database decides the role, never the token."""
    forged = create_token(
        uuid.UUID(account["user"]["id"]), "admin", ACCESS, timedelta(minutes=30)
    )

    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 403, response.text


def test_a_promoted_user_reaches_admin_endpoints_with_an_older_token(client, db, account, auth):
    user = db.scalar(select(User).where(User.email == account["email"]))
    user.role = "admin"
    db.commit()

    # The Phase 2 admin endpoint is still a stub, so a 501 (instead of 401/403)
    # proves the admin dependency let the request through.
    response = client.get("/api/v1/users", headers=auth)

    assert response.status_code == 501, response.text


def test_disabling_an_account_invalidates_its_existing_token(client, db, account, auth):
    user = db.scalar(select(User).where(User.email == account["email"]))
    user.is_active = False
    db.commit()

    response = client.get("/api/v1/users/me", headers=auth)

    assert response.status_code == 401, response.text


def test_register_and_login_never_leak_the_hash(client, account, tokens):
    assert "password" not in " ".join(tokens)
    assert "$argon2" not in str(tokens)
