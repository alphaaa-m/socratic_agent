"""Helpers and fixtures for the Phase 2 acceptance tests."""

import pytest

from tests.phase_1.conftest import PASSWORD, login, register


def authorization_for(client, email: str, password: str = PASSWORD) -> dict[str, str]:
    tokens = login(client, email, password)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def account(client):
    user = register(client)
    return {"user": user, "email": user["email"], "password": PASSWORD}


@pytest.fixture
def auth(client, account):
    return authorization_for(client, account["email"], account["password"])
