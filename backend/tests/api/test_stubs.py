"""Unfinished endpoints still answer 501 instead of crashing.

Phase 1 implemented /auth/* and /users/me, so this test now uses an endpoint
that still belongs to a later phase (starting a session is Phase 2).
"""


def _access_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Stub User", "email": "stub@example.com", "password": "Secret123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "stub@example.com", "password": "Secret123"},
    )
    return response.json()["access_token"]


def test_unfinished_endpoint_returns_501(client):
    token = _access_token(client)

    response = client.post(
        "/api/v1/sessions",
        json={"subject_id": "00000000-0000-0000-0000-000000000001"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 501, response.text
    assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"
