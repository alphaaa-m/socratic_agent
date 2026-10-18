"""FR-ACC-01/02: the caller's own account (docs Sec 9.17, Sec 18.4)."""

import uuid

import pytest
from sqlalchemy import select

from app.models import LearnerProfile, User
from tests.phase_1.conftest import login

pytestmark = pytest.mark.phase1


def test_me_returns_the_caller(client, account, auth):
    response = client.get("/api/v1/users/me", headers=auth)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == account["user"]["id"]
    assert body["email"] == account["email"]
    assert "password_hash" not in body


def test_me_requires_authentication(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_rejects_an_unknown_bearer_token(client):
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401, response.text


def test_update_own_name(client, auth):
    response = client.patch("/api/v1/users/me", json={"name": "Amina A. Yusuf"}, headers=auth)

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Amina A. Yusuf"

    # The change is persisted, not just echoed.
    assert client.get("/api/v1/users/me", headers=auth).json()["name"] == "Amina A. Yusuf"


def test_update_name_rejects_an_empty_name(client, auth):
    response = client.patch("/api/v1/users/me", json={"name": ""}, headers=auth)

    assert response.status_code == 422, response.text


def test_change_password_then_login_with_the_new_password(client, account, auth):
    response = client.post(
        "/api/v1/users/me/password",
        json={"current_password": account["password"], "new_password": "BrandNew123"},
        headers=auth,
    )

    assert response.status_code == 204, response.text
    tokens = login(client, account["email"], "BrandNew123")
    assert tokens["access_token"]


def test_change_password_rejects_a_wrong_current_password(client, account, auth):
    response = client.post(
        "/api/v1/users/me/password",
        json={"current_password": "NotMyPassword1", "new_password": "BrandNew123"},
        headers=auth,
    )

    assert response.status_code == 400, response.text
    assert response.json()["error"]["code"] == "BAD_REQUEST"

    # The old password still works.
    assert login(client, account["email"], account["password"])["access_token"]


def test_change_password_rejects_a_weak_new_password(client, account, auth):
    response = client.post(
        "/api/v1/users/me/password",
        json={"current_password": account["password"], "new_password": "weak"},
        headers=auth,
    )

    assert response.status_code == 422, response.text


def test_read_own_learner_profile(client, auth):
    response = client.get("/api/v1/users/me/profile", headers=auth)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["current_level"] == "beginner"
    assert body["learning_preferences"] == {}


def test_update_learning_preferences(client, auth):
    preferences = {"explanation_style": "examples", "language": "en"}

    response = client.patch(
        "/api/v1/users/me/profile",
        json={"learning_preferences": preferences},
        headers=auth,
    )

    assert response.status_code == 200, response.text
    assert response.json()["learning_preferences"] == preferences


def test_delete_account_removes_the_user_and_all_personal_data(client, db, account, auth):
    user_id = uuid.UUID(account["user"]["id"])

    response = client.delete("/api/v1/users/me", headers=auth)

    assert response.status_code == 204, response.text
    # The old token is dead and the account can no longer sign in.
    assert client.get("/api/v1/users/me", headers=auth).status_code == 401
    rejected = client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": account["password"]},
    )
    assert rejected.status_code == 401, rejected.text
    # The user row and the cascaded profile row are gone.
    assert db.scalar(select(User).where(User.id == user_id)) is None
    assert db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user_id)) is None
