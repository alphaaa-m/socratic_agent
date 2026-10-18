"""FR-LOG-01..04: login, and the login rate limit (docs Sec 9.2, Sec 18.3, Sec 26)."""

import pytest
from sqlalchemy import select

from app.models import User
from tests.phase_1.conftest import PASSWORD, login

pytestmark = pytest.mark.phase1


def test_login_returns_a_token_pair(client, account):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": account["password"]},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]
    assert body["token_type"] == "bearer"
    # Sec 26: access tokens live 30 minutes.
    assert body["expires_in"] == 30 * 60


def test_login_accepts_a_case_variant_of_the_email(client, account):
    tokens = login(client, account["email"].upper())
    assert tokens["access_token"]


def test_login_uses_the_same_error_for_unknown_email_and_wrong_password(client, account):
    """FR-LOG-02: no hint about which email addresses exist."""
    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": PASSWORD},
    )
    wrong = client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": "WrongPass123"},
    )

    assert unknown.status_code == 401, unknown.text
    assert wrong.status_code == 401, wrong.text
    assert unknown.json()["error"]["message"] == wrong.json()["error"]["message"]
    assert unknown.json()["error"]["code"] == "UNAUTHENTICATED"


def test_login_rejects_an_inactive_account(client, db, account):
    """FR-LOG-03."""
    user = db.scalar(select(User).where(User.email == account["email"]))
    user.is_active = False
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": account["password"]},
    )

    assert response.status_code == 401, response.text


def test_login_rejects_a_malformed_body(client, account):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": ""},
    )

    assert response.status_code == 422, response.text


def test_login_is_rate_limited_after_five_attempts(client, account):
    """FR-LOG-04: five attempts per minute for the same address and email."""
    for attempt in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": account["email"], "password": "WrongPass123"},
        )
        assert response.status_code == 401, f"attempt {attempt}: {response.text}"

    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": "WrongPass123"},
    )

    assert blocked.status_code == 429, blocked.text
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"
    assert blocked.headers["Retry-After"] == "60"


def test_rate_limit_is_per_email(client, account):
    """Six failures on one account must not block a different account."""
    for _ in range(6):
        client.post(
            "/api/v1/auth/login",
            json={"email": account["email"], "password": "WrongPass123"},
        )

    from tests.phase_1.conftest import register

    register(client, email="other@example.com", name="Other Student")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": PASSWORD},
    )

    assert response.status_code == 200, response.text
