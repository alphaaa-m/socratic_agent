"""FR-JWT-01..06: token contents, refresh flow and rejection of bad tokens."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.auth.jwt import ACCESS, REFRESH, create_token, decode_token
from app.core.config import get_settings
from app.core.exceptions import UnauthenticatedError

pytestmark = pytest.mark.phase1


def test_created_token_has_the_required_claims(account):
    user_id = uuid.UUID(account["user"]["id"])

    token = create_token(user_id, "student", ACCESS, timedelta(minutes=30))
    payload = decode_token(token, expected_type=ACCESS)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "student"
    assert payload["type"] == ACCESS
    assert payload["jti"]
    assert payload["iat"] and payload["exp"]


def test_decode_rejects_a_refresh_token_used_as_an_access_token(account):
    token = create_token(uuid.uuid4(), "student", REFRESH, timedelta(days=7))

    with pytest.raises(UnauthenticatedError) as excinfo:
        decode_token(token, expected_type=ACCESS)

    assert excinfo.value.code == "TOKEN_INVALID"


def test_decode_rejects_an_expired_token():
    token = create_token(uuid.uuid4(), "student", ACCESS, timedelta(seconds=-30))

    with pytest.raises(UnauthenticatedError) as excinfo:
        decode_token(token, expected_type=ACCESS)

    assert excinfo.value.code == "TOKEN_EXPIRED"


def test_decode_rejects_a_token_signed_with_another_secret():
    now = datetime.now(UTC)
    forged = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "role": "admin",
            "type": ACCESS,
            "iat": now,
            "exp": now + timedelta(minutes=30),
            "jti": uuid.uuid4().hex,
        },
        "a-completely-different-secret-key",
        algorithm="HS256",
    )

    with pytest.raises(UnauthenticatedError) as excinfo:
        decode_token(forged, expected_type=ACCESS)

    assert excinfo.value.code == "TOKEN_INVALID"


@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c"])
def test_decode_rejects_garbage(token):
    with pytest.raises(UnauthenticatedError):
        decode_token(token, expected_type=ACCESS)


def test_decode_rejects_a_token_without_the_required_claims():
    settings = get_settings()
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": ACCESS},
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(UnauthenticatedError) as excinfo:
        decode_token(token, expected_type=ACCESS)

    assert excinfo.value.code == "TOKEN_INVALID"


def test_decode_rejects_a_subject_that_is_not_a_uuid():
    settings = get_settings()
    token = jwt.encode(
        {"sub": "not-a-uuid", "type": ACCESS, "jti": "x"},
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(UnauthenticatedError) as excinfo:
        decode_token(token, expected_type=ACCESS)

    assert excinfo.value.code == "TOKEN_INVALID"


def test_refresh_returns_a_fresh_pair(client, tokens):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["access_token"] != tokens["access_token"]


def test_refresh_rejects_an_access_token(client, tokens):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})

    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "TOKEN_INVALID"


def test_refresh_rejects_a_garbage_token(client):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-jwt"})

    assert response.status_code == 401, response.text


def test_authorization_header_rejects_a_refresh_token(client, tokens):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )

    assert response.status_code == 401, response.text
