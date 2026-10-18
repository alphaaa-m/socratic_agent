import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]

# The tests run against the SAME local PostgreSQL database as the app (there is
# no separate test database -- see docs/phase-0 guide). The local .env therefore
# has to win over the fallback below. load_dotenv() never overwrites a variable
# that is already set, which is exactly what CI relies on (CI exports its own
# DATABASE_URL/JWT_SECRET and those stay authoritative).
load_dotenv(BACKEND_DIR / ".env")

# Tests must always be deterministic: never call a real LLM and never treat a
# test run as a production environment.
os.environ["APP_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "fake"
os.environ["LLM_MODEL"] = "fake"
os.environ.setdefault(
    "DATABASE_URL", "postgresql://postgres:postgres123@localhost:5432/socratic_agent"
)
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-12")

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.agents.llm_gateway import FakeGateway
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.database.session import get_db
from app.main import create_app

# The imports above must come *after* the environment setup: app.database.session
# builds the engine while it is imported, so DATABASE_URL has to be final first.


@pytest.fixture(scope="session")
def engine():
    url = get_settings().database_url
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    return create_engine(url)


@pytest.fixture
def db(engine):
    """A session that runs inside a savepoint, so every test is rolled back.

    `join_transaction_mode="create_savepoint"` means the services under test can
    call commit() freely: the savepoint is released, the outer transaction is
    rolled back when the test ends, and the shared database keeps its data.
    """
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
    # The limiter is a process-wide singleton, so counters would leak from one
    # test into the next. Reset the storage before every test.
    limiter.reset()
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        app.state.agent.gateway = fake_gateway
        yield c
