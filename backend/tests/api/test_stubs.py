def test_unfinished_endpoint_returns_501(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"name": "A", "email": "a@b.co", "password": "Secret123"},
    )
    assert r.status_code == 501 and r.json()["error"]["code"] == "NOT_IMPLEMENTED"
