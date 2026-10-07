import os

os.environ.setdefault("APP_ENV", "test")
# Single shared database (no separate test DB): ensure schema exists, never drop.
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres123@localhost:5432/socratic_agent")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-12")
os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("LLM_MODEL", "fake")

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.agents.llm_gateway import FakeGateway
from app.core.config import get_settings
from app.database.session import get_db
from app.main import create_app


@pytest.fixture(scope="session")
def engine():
    url = get_settings().database_url
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    return create_engine(url)


@pytest.fixture
def db(engine):
    conn = engine.connect()
    tx = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    yield session
    session.close()
    tx.rollback()
    conn.close()


@pytest.fixture
def fake_gateway():
    return FakeGateway()


@pytest.fixture
def client(db, fake_gateway):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        app.state.agent.gateway = fake_gateway
        yield c
