"""Shared helpers and fixtures for the Phase 1 (authentication) tests."""

import pytest

PASSWORD = "Secret123"


def register(client, email="amina@example.com", name="Amina Yusuf", password=PASSWORD):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client, email="amina@example.com", password=PASSWORD):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def account(client):
    """A registered student that is ready to sign in."""
    user = register(client)
    return {"user": user, "email": user["email"], "password": PASSWORD}


@pytest.fixture
def tokens(client, account):
    """The access/refresh token pair for `account`."""
    return login(client, account["email"], account["password"])


@pytest.fixture
def auth(tokens):
    """An Authorization header built from the access token."""
    return {"Authorization": f"Bearer {tokens['access_token']}"}
