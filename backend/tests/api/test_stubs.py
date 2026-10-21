"""Unfinished endpoints still answer 501 instead of crashing.

Phase 2 implemented sessions and subjects, so this test now uses an endpoint
that still belongs to a later phase (ending a session is Phase 6).
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
    """POST /sessions/{id}/end is a Phase-6 stub -- still returns 501."""
    token = _access_token(client)

    # The session id does not need to exist for the stub guard to fire first.
    response = client.post(
        "/api/v1/sessions/00000000-0000-0000-0000-000000000001/end",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 501, response.text
    assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"
