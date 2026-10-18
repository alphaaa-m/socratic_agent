"""FR-REG-01..06: registration (docs Sec 9.1, Sec 18.3)."""

import pytest

from tests.phase_1.conftest import PASSWORD, login, register

pytestmark = pytest.mark.phase1


def test_register_returns_the_new_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Amina Yusuf", "email": "amina@example.com", "password": PASSWORD},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Amina Yusuf"
    assert body["email"] == "amina@example.com"
    # FR-REG-06: a visitor can only ever create a student.
    assert body["role"] == "student"
    assert body["is_active"] is True
    assert body["id"] and body["created_at"]


def test_register_never_returns_the_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Amina", "email": "amina@example.com", "password": PASSWORD},
    )

    body = response.json()
    assert "password" not in body
    assert "password_hash" not in body
    assert PASSWORD not in response.text


def test_register_lowercases_the_email(client):
    """FR-REG-03: the stored email (and therefore login) is case-insensitive."""
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Amina", "email": "Amina@Example.COM", "password": PASSWORD},
    )

    assert response.status_code == 201, response.text
    assert response.json()["email"] == "amina@example.com"

    # Logging in with the mixed-case spelling must work too.
    tokens = login(client, "Amina@Example.COM", PASSWORD)
    assert tokens["access_token"]


def test_register_creates_a_learner_profile(client):
    """FR-REG-05: the profile row is created in the same transaction."""
    register(client)
    tokens = login(client)

    response = client.get(
        "/api/v1/users/me/profile",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200, response.text
    profile = response.json()
    assert profile["current_level"] == "beginner"
    # The schema default for a brand new learner (models/learner_profile.py).
    assert profile["level_score"] == 0.3
    assert profile["assessment_count"] == 0
    assert profile["total_sessions"] == 0


def test_register_rejects_a_duplicate_email(client):
    """FR-REG-02."""
    register(client)

    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Someone Else", "email": "amina@example.com", "password": PASSWORD},
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "CONFLICT"


def test_register_rejects_a_duplicate_email_in_another_case(client):
    register(client)

    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Someone Else", "email": "AMINA@EXAMPLE.COM", "password": PASSWORD},
    )

    assert response.status_code == 409, response.text


def test_register_rejects_a_weak_password(client):
    """FR-REG-04: 8-128 characters with at least one letter and one digit."""
    for password in ("short1", "onlyletters", "12345678", "lettersonly"):
        response = client.post(
            "/api/v1/auth/register",
            json={"name": "Amina", "email": "amina@example.com", "password": password},
        )
        assert response.status_code == 422, f"{password!r} should be rejected: {response.text}"
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_rejects_an_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Amina", "email": "not-an-email", "password": PASSWORD},
    )

    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_rejects_an_empty_name(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "", "email": "amina@example.com", "password": PASSWORD},
    )

    assert response.status_code == 422, response.text
