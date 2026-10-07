def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["database"] == "ok"
