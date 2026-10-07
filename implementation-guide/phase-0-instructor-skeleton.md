# Phase 0: Database and Project Skeleton (Instructor)

*[Index](README.md) | [Next: Phase 1 →](phase-1-authentication.md)*

**Owner:** Instructor. **Time:** 2-3 days.

## 0.1 Goal

Build the base that all student phases use. At the end of Phase 0, a student can clone the repository, run one command set, and get a working but empty system: the database exists with all tables, the backend starts, the frontend starts, and every unfinished feature is a clearly marked stub.

## 0.2 Deliverables

| # | Deliverable | Done when |
|---|---|---|
| 1 | Local PostgreSQL (single `socratic_agent` database, no Docker) | `pg_isready` works. The database exists. |
| 2 | Complete schema: 9 tables, constraints, indexes, triggers | `alembic upgrade head` creates the schema in §7.1. `alembic check` is clean. |
| 3 | SQLAlchemy models (complete) | All models from §7.2 are in `app/models/`. |
| 4 | Seed and admin scripts | `scripts/seed.py` and `scripts/create_admin.py` work. |
| 5 | Backend skeleton | App starts. `/api/v1/health` works. Config, errors, logging, request ID are complete. |
| 6 | API contract | All Pydantic schemas (§18.12) are complete. All routers exist and return `501` for unfinished endpoints. |
| 7 | Agent contracts | `app/agents/schemas.py`, `LLMGateway` protocol, `FakeGateway`, `NullRetriever` are complete. Capability classes are stubs. |
| 8 | Test setup | `tests/conftest.py` with database, client and fake-gateway fixtures. Sample tests pass. |
| 9 | Frontend skeleton | Next.js app with Tailwind, shadcn/ui, layout, sidebar, placeholder pages, React Query provider, types, BFF stubs. |
| 10 | CI | GitHub Actions run lint, migration check and tests for both apps. |
| 11 | Student onboarding | `README.md`, `docs/` (the design document), PR template, `CONTRIBUTING.md`. |

## 0.3 Repository Layout

Legend: ✅ complete (student does not change it) · 🧩 stub (student implements it) · 📝 student adds files here.

```text
socratic-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                       ✅
│   │   ├── api/
│   │   │   ├── deps.py                   🧩 get_current_user (phase 1). get_db is ✅
│   │   │   └── v1/  router.py ✅  health.py ✅
│   │   │            auth.py users.py subjects.py sessions.py messages.py
│   │   │            assessments.py progress.py documents.py            🧩 (return 501)
│   │   ├── models/                       ✅ all 9 models + enums
│   │   ├── schemas/                      ✅ all request and response schemas
│   │   ├── services/                     🧩 one class for each area (methods raise NotImplementedError)
│   │   ├── agents/
│   │   │   ├── schemas.py                ✅
│   │   │   ├── llm_gateway.py            ✅ protocol + FakeGateway.   LangChainGateway 🧩
│   │   │   ├── llm_factory.py            🧩 (phase 4)
│   │   │   ├── factory.py                ✅ build_agent (uses FakeGateway until phase 4)
│   │   │   ├── socratic_agent.py         🧩
│   │   │   ├── capabilities/             🧩 10 files (class + method signatures only)
│   │   │   └── prompts/                  📝
│   │   ├── rag/                          🧩 (phase 7). NullRetriever ✅
│   │   ├── database/                     ✅ base.py, session.py
│   │   ├── auth/                         ✅ passwords.py    🧩 jwt.py (phase 1)
│   │   └── core/                         ✅ config, exceptions, logging, rate_limit
│   ├── alembic/ + alembic.ini            ✅
│   ├── scripts/                          ✅ seed.py, create_admin.py   🧩 reindex.py (phase 7)
│   ├── tests/                            ✅ conftest.py, sample tests. 📝 tests/phase_N/
│   ├── requirements.txt  .env.example    ✅
├── frontend/
│   ├── app/                              ✅ layouts. 🧩 pages (placeholders)
│   │   └── api/                          🧩 BFF route handlers (return 501)
│   ├── components/ui/                    ✅ shadcn
│   ├── components/layout/                ✅ Sidebar, Header
│   ├── components/todo-page.tsx          ✅ "TODO phase N" placeholder
│   ├── services/ hooks/ lib/             ✅ http.ts, query client. 📝 feature files
│   ├── types/api.ts                      ✅
│   └── middleware.ts                     🧩 (phase 1)
├── .github/workflows/ci.yml              ✅ (apt PostgreSQL + uv, no Docker)
├── docs/                                 ✅ copy of socratic-agent-docs/
├── .github/workflows/ci.yml              ✅
├── .github/pull_request_template.md      ✅
├── CONTRIBUTING.md  README.md            ✅
```

## 0.4 Step-by-Step

### Step 1: Repository

```bash
mkdir socratic-agent && cd socratic-agent && git init -b main
mkdir backend frontend docs .github/workflows
cp -r <path>/socratic-agent-docs/* docs/
```

Add a `.gitignore` for Python, Node, `.env`, `.env.local`, `data/`, `.venv/`, `.next/`, `node_modules/`. On GitHub, protect `main`: pull request required, one review, CI must pass.

### Step 2: PostgreSQL

Use the local PostgreSQL service (no Docker). There is one database for everything, including tests (tests use savepoint rollback, so they never touch committed data).

```bash
psql -U postgres -c "CREATE DATABASE socratic_agent OWNER postgres"
pg_isready -h localhost -p 5432        # must report "accepting connections"
psql -U postgres -l                    # socratic_agent must show
```

### Step 3: Backend base

```bash
cd backend
uv venv
# create requirements.txt from the design document §19.6
uv pip install -r requirements.txt
mkdir -p app/{api/v1,models,schemas,services,agents/{capabilities,prompts},rag,database,auth,core} \
         scripts tests/{unit,api,db,integration,rag,ai}
find app tests -type d -exec touch {}/__init__.py \;
```

Create these files **complete**:

| File | Source |
|---|---|
| `app/core/config.py` | §19.3 (`Settings`) |
| `app/database/base.py` | §7.2 (`Base`, naming convention, mixins) |
| `app/models/*.py`, `app/models/__init__.py` | §7.2 (all models) |
| `app/core/exceptions.py` | §27.3 (add `NotImplementedError` handler, see below) |
| `app/main.py` | §19.4 (use `build_agent` from `app/agents/factory.py`) |

`app/database/session.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True, pool_size=5, max_overflow=5)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db
```

`app/core/logging.py` (JSON logs and request ID):

```python
import logging, uuid
from starlette.middleware.base import BaseHTTPMiddleware


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = uuid.uuid4().hex[:16]
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response
```

`app/core/rate_limit.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
```

Add the **stub handler** to `register_exception_handlers`. This turns every unfinished feature into a clear `501`:

```python
class NotImplementedYet(AppError):
    status_code, code = 501, "NOT_IMPLEMENTED"

@app.exception_handler(NotImplementedError)
async def not_implemented(request, exc: NotImplementedError):
    return error_response(request, 501, "NOT_IMPLEMENTED", str(exc) or "Not implemented yet.", [])
```

Health endpoint (complete):

```python
# app/api/v1/health.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.api.deps import DB
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DB):
    result = {"status": "ok", "database": "ok", "vector_store": "disabled"}
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        result.update(status="error", database="error")
        return JSONResponse(result, status_code=503)
    return result
```

### Step 4: Alembic and the schema

```bash
alembic init alembic
```

`alembic/env.py` (key parts):

```python
from alembic import context
from sqlalchemy import engine_from_config, pool
import app.models                                   # registers all models
from app.core.config import get_settings
from app.database.base import Base

config = context.config
config.set_main_option("sqlalchemy.url",
                       config.get_main_option("sqlalchemy.url") or get_settings().database_url)
target_metadata = Base.metadata
# run_migrations_online(): use engine_from_config(...) with compare_type=True in context.configure
```

Create the migration and **check it against the SQL in §7.1**:

```bash
alembic revision --autogenerate -m "initial schema"
```

Then edit the generated file by hand:

1. Add the `set_updated_at()` function and the three triggers with `op.execute(...)` (use the SQL from §7.1). Add `op.execute("DROP TRIGGER ...")` and `DROP FUNCTION` in `downgrade()`.
2. Check each table: columns, `CHECK` names, unique names, foreign keys with `ON DELETE`, indexes (including `started_at DESC`).
3. Check `document_chunks.vector_id` is `GENERATED ALWAYS AS IDENTITY`.

```bash
uv run alembic upgrade head
uv run alembic check                 # must say: No new upgrade operations detected
uv run alembic downgrade base && uv run alembic upgrade head  # round trip must work
psql -U postgres -d socratic_agent -c '\dt'   # 9 tables + alembic_version
```

> **Verification tip:** also run the raw SQL from §7.1 on an empty scratch database. Compare with `pg_dump --schema-only` of the Alembic database. The constraint and index names must match.

### Step 5: Seed and admin scripts

```python
# scripts/seed.py
from sqlalchemy import select
from app.database.session import SessionLocal
from app.models import Subject

SUBJECTS = [
    ("Python Programming", "Variables, control flow, functions, data structures and common pitfalls."),
    ("Basic Mathematics", "Fractions, algebra basics, and number sense."),
    ("Introduction to Databases", "Tables, keys, SQL queries and normalization."),
]

with SessionLocal() as db, db.begin():
    for name, description in SUBJECTS:
        if not db.scalar(select(Subject).where(Subject.name == name)):
            db.add(Subject(name=name, description=description))
print("seed done")
```

```python
# scripts/create_admin.py
import argparse, getpass
from sqlalchemy import select
from app.auth.passwords import hash_password            # student implements in phase 1
from app.database.session import SessionLocal
from app.models import LearnerProfile, User

parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True)
parser.add_argument("--name", default="Administrator")
args = parser.parse_args()
password = getpass.getpass("Password: ")

with SessionLocal() as db, db.begin():
    user = db.scalar(select(User).where(User.email == args.email.lower()))
    if user is None:
        user = User(name=args.name, email=args.email.lower(), password_hash=hash_password(password), role="admin")
        db.add(user); db.flush()
        db.add(LearnerProfile(user_id=user.id))
    else:
        user.role = "admin"
print("admin ready")
```

> `create_admin.py` needs `hash_password`. In Phase 0, implement `app/auth/passwords.py` completely (it is 10 lines, §19.4.1) so that you can create the admin. In Phase 1 the student writes the **tests** for it and the JWT code. The layout in 0.3 already shows `passwords.py` as complete.

### Step 6: API contract (Pydantic schemas)

Create the files in `app/schemas/` from §18.12. Cover **every** schema that the endpoint tables in §18 name:

`ORMModel`, `Page[T]`, `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `TokenResponse`, `UserResponse`, `UserUpdateRequest`, `PasswordChangeRequest`, `AdminUserUpdateRequest`, `LearnerProfileResponse`, `LearnerProfileUpdateRequest`, `SubjectCreateRequest`, `SubjectUpdateRequest`, `SubjectResponse`, `SessionCreateRequest`, `SessionResponse`, `SessionDetailResponse`, `SessionSummaryResponse`, `SendMessageRequest`, `MessageResponse`, `SendMessageResponse`, `HintResponse`, `SessionStateResponse`, `AssessmentResponse`, `ProgressResponse`, `ProgressOverviewResponse`, `SubjectProgressResponse`, `DocumentResponse`, `ChunkResponse`, `RetrievalTestRequest`, `RetrievedChunkResponse`.

Rule: do not leave a schema undefined. The routers import them, and the OpenAPI page (`/docs`) must show the full contract.

### Step 7: Routers and stubs

Create each router file with all endpoints from §18.3-§18.11. Each endpoint has the correct path, `response_model`, status code and auth dependency. The body calls a service method.

```python
# app/api/v1/subjects.py  (example of the stub pattern)
@router.get("", response_model=list[SubjectResponse])
def list_subjects(user: CurrentUser, db: DB, active_only: bool = True):
    return SubjectService(db).list(active_only)
```

```python
# app/services/subject_service.py
class SubjectService:
    def __init__(self, db: Session):
        self.db = db

    def list(self, active_only: bool = True) -> list[Subject]:
        raise NotImplementedError("TODO(phase-2): list subjects (filter by is_active)")
```

Rules for stubs:

- Every stub message starts with `TODO(phase-N):` and says in one line what to do.
- Every service method that students implement has full type hints and a docstring with the business rule and the requirement ID (for example, `FR-SUB-01`).
- `get_current_user` in `app/api/deps.py` raises `NotImplementedError("TODO(phase-1): ...")`. Endpoints that need a user will return `501` until Phase 1 is done. The health endpoint does not need a user.

Stub tables (create the same list in the code):

| Service | Methods | Phase |
|---|---|---|
| `AuthService` | `register`, `login`, `refresh` | 1 |
| `UserService` | `get_profile`, `update_me`, `change_password`, `delete_me`, `update_profile`, `list_users`, `admin_update` | 1 (account), 2 (admin) |
| `SubjectService` | `list`, `get`, `create`, `update`, `delete` | 2 |
| `SessionService` | `create`, `list`, `get`, `end_session` | 2 (create, list, get), 6 (end) |
| `TutoringService` | `list_messages`, `handle_student_message`, `handle_hint_request` | 3 |
| `AssessmentService` | `list_for_session`, `get` | 5 |
| `ProgressService` | `overview`, `for_subject`, `apply_session_result` | 6 |
| `DocumentService` | `upload`, `list`, `get`, `delete`, `reindex`, `chunks`, `search` | 7 |

### Step 8: Agent contracts

Complete files:

- `app/agents/schemas.py` from §14.3.
- `app/agents/llm_gateway.py`: the `LLMGateway` protocol (§16.7) and the `FakeGateway` below. `LangChainGateway` is a stub (phase 4).
- `app/agents/factory.py`: `build_agent(settings)` returns `SocraticAgent(FakeGateway(), NullRetriever(), settings)` while `LLM_PROVIDER=fake`.
- `app/rag/retriever.py`: `NullRetriever` only.

Add `fake` to the allowed values of `llm_provider` in `Settings` (used for tests and Phase 3).

```python
# app/agents/llm_gateway.py  (FakeGateway)
from app.agents.schemas import EvaluationResult, SessionSummary, TutorReply
from app.core.exceptions import LLMUnavailableError


class FakeGateway:
    """Deterministic gateway for tests and for phase 3."""

    def __init__(self):
        self.calls: list[tuple[str, list]] = []
        self.eval_queue: list[EvaluationResult] = []
        self.reply_queue: list[TutorReply] = []
        self._fail: set[str] = set()

    def fail_next(self, method: str) -> None:
        self._fail.add(method)

    def _enter(self, name, messages):
        self.calls.append((name, messages))
        if name in self._fail:
            self._fail.discard(name)
            raise LLMUnavailableError()

    def evaluate(self, messages):
        self._enter("evaluate", messages)
        return self.eval_queue.pop(0) if self.eval_queue else EvaluationResult(
            correctness_score=0.5, reasoning_score=0.5, confidence_score=0.5,
            feedback="Good effort.", addresses_core_question=False)

    def generate_reply(self, messages):
        self._enter("generate_reply", messages)
        return self.reply_queue.pop(0) if self.reply_queue else TutorReply(
            message="What do you already know about this topic?", message_type="guidance")

    def summarize_session(self, messages):
        self._enter("summarize_session", messages)
        return SessionSummary(outcome="partial", overview="Fake summary.", key_concepts=[], strengths=[],
                              misconceptions_addressed=[], areas_to_review=[], next_steps=[])

    def summarize_memory(self, messages):
        self._enter("summarize_memory", messages)
        return "Fake memory summary."
```

`app/agents/socratic_agent.py` and the 10 capability files contain the class and the method signatures from §14.4 and §3.5 with `raise NotImplementedError("TODO(phase-N): ...")`. Mark the phase in each message (4 for dialogue, hints, memory, prompts; 5 for evaluator, misconceptions, adaptive, level; 6 for summarizer; 7 for retriever wrapper).

### Step 9: Test setup

```python
# tests/conftest.py
import os
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.environ.setdefault("APP_ENV", "test")
# Single shared database (no separate test DB): ensure schema exists, never drop it.
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres123@localhost:5432/socratic_agent")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-12")
os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("LLM_MODEL", "fake")

from app.agents.llm_gateway import FakeGateway          # noqa: E402
from app.core.config import get_settings                # noqa: E402
from app.database.session import get_db                 # noqa: E402
from app.main import create_app                         # noqa: E402


@pytest.fixture(scope="session")
def engine():
    url = get_settings().database_url
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")   # ensure schema exists; never downgrade the shared DB
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
        app.state.agent.dialogue.gateway = fake_gateway      # adjust to your agent wiring
        yield c
```

Sample tests (all must pass at handover):

```python
# tests/api/test_health.py
def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["database"] == "ok"

# tests/api/test_stubs.py
def test_unfinished_endpoint_returns_501(client):
    r = client.post("/api/v1/auth/register", json={"name": "A", "email": "a@b.co", "password": "Secret123"})
    assert r.status_code == 501 and r.json()["error"]["code"] == "NOT_IMPLEMENTED"

# tests/db/test_constraints.py  (3 examples; add one test for each CHECK type)
def test_email_must_be_lowercase(db):
    db.add(User(name="A", email="A@B.CO", password_hash="x"))
    with pytest.raises(IntegrityError):
        db.flush()
```

> The wiring of `fake_gateway` depends on how you build `SocraticAgent`. Make `build_agent` accept an optional gateway argument so tests can inject it cleanly. Do this in Phase 0, because students must not guess it.

### Step 10: Frontend base

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir=false --import-alias "@/*"
npx shadcn@latest init
npx shadcn@latest add button card input textarea label form badge progress tabs table dialog \
  alert-dialog alert dropdown-menu select sheet scroll-area skeleton sonner switch separator avatar
npm install @tanstack/react-query react-hook-form zod @hookform/resolvers recharts
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom msw @playwright/test jest-axe
echo 'BACKEND_API_URL=http://localhost:8000/api/v1' > .env.local
```

Create these **complete** files:

| File | Content |
|---|---|
| `types/api.ts` | §20.5 plus all other types that mirror the backend schemas |
| `lib/query-client.ts`, `app/providers.tsx` | React Query provider (client component) wrapped in `app/layout.tsx` with `<Toaster />` |
| `services/http.ts` | `api<T>(path, init)`: calls `/api/proxy/<path>`, parses JSON, throws a typed `ApiError` from the standard error body |
| `components/layout/Sidebar.tsx`, `Header.tsx` | Navigation links for all pages (Dashboard, Subjects, Sessions, Progress, Admin) |
| `components/todo-page.tsx` | Placeholder component `<TodoPage phase={3} title="Chat" />` |
| `app/(app)/layout.tsx` | App shell with sidebar and header |

Create these **stubs**:

| File | Stub behavior |
|---|---|
| `app/(auth)/login/page.tsx`, `register/page.tsx` | `<TodoPage phase={1} .../>` |
| `app/(app)/dashboard`, `subjects`, `sessions`, `sessions/[sessionId]`, `progress`, `admin/*` pages | `<TodoPage phase={N} .../>` with the right phase |
| `app/api/auth/login/route.ts`, `logout/route.ts`, `app/api/proxy/[...path]/route.ts` | Return `NextResponse.json({error:{code:"NOT_IMPLEMENTED",message:"TODO(phase-1)"}}, {status:501})` |
| `middleware.ts` | Empty `middleware` function with `// TODO(phase-1): redirect to /login when no session cookie` and a `matcher` |

Check: `npm run dev` shows the app shell, every page shows a "TODO phase N" box, `npm run lint`, `npx tsc --noEmit` and `npm test` (one smoke test for `TodoPage`) pass.

### Step 11: CI

Use the workflow from §28.8 (apt-installed PostgreSQL + `uv`, no Docker). Change the backend env: `LLM_PROVIDER: fake`, `LLM_MODEL: fake`, `DATABASE_URL` for the single `socratic_agent` database. Keep the coverage gate off until Phase 8 (`--cov-fail-under` removed).

### Step 12: Student onboarding files

- `README.md` (root): prerequisites, setup commands (§32.3-§32.8), how to find work (`grep TODO(phase-N)`), link to `docs/` and to this guide.
- `CONTRIBUTING.md`: the working rules from the guide index.
- `.github/pull_request_template.md`: the template from the guide index.
- `docs/implementation-guide/`: a copy of this guide.

### Step 13 (Recommended): Phase acceptance tests

Write failing tests for each student phase in advance. The student's job is to make them pass. Mark them so that CI stays green until the phase starts:

```python
# tests/phase_1/test_auth.py
import pytest
pytestmark = pytest.mark.phase1          # run with: pytest -m phase1
```

In `pytest.ini`, set `addopts = -m "not phase1 and not phase2 and ..."` for CI on `main`, and run `pytest -m phaseN` on the student's branch. Suggested test files:

| Phase | Test files |
|---|---|
| 1 | `test_register.py`, `test_login.py`, `test_refresh.py`, `test_users_me.py`, `test_passwords_jwt.py` (unit) |
| 2 | `test_subjects.py`, `test_sessions.py`, `test_admin_users.py` |
| 3 | `test_messages_list.py`, `test_send_message.py`, `test_turn_conflict.py`, `test_hints.py` |
| 4 | `test_leak_guard.py`, `test_prompt_builder.py`, `test_dialogue_engine.py`, `test_memory.py` |
| 5 | `test_adaptive_controller.py`, `test_level_estimator.py`, `test_evaluator.py`, `test_example_session.py` |
| 6 | `test_end_session.py`, `test_mastery.py`, `test_progress_api.py`, `test_delete_account.py` |
| 7 | `test_chunking.py`, `test_faiss_store.py`, `test_ingestion.py`, `test_retriever.py`, `test_documents_api.py` |

## 0.5 Handover Checklist

Run this on a **fresh clone** on another machine before you give the repository to students.

- [ ] Local PostgreSQL is running (`pg_isready`). The `socratic_agent` database exists.
- [ ] `cd backend && uv venv && uv pip install -r requirements.txt` works.
- [ ] `uv run alembic upgrade head` creates 9 tables. `uv run alembic check` is clean. Downgrade and upgrade work.
- [ ] The schema matches §7.1 (constraint and index names compared).
- [ ] `uv run python scripts/seed.py` creates 3 subjects. `uv run python scripts/create_admin.py --email ...` creates an admin.
- [ ] `uv run uvicorn app.main:app --reload` starts. `/api/v1/health` returns `ok`. `/docs` shows **all** endpoints and schemas.
- [ ] An unfinished endpoint returns `501 NOT_IMPLEMENTED` with the TODO text.
- [ ] `uv run pytest -q` passes. `uv run ruff check .` passes.
- [ ] `cd frontend && npm install && npm run dev` starts. All pages show their TODO placeholder.
- [ ] `npm run lint`, `npx tsc --noEmit`, `npm test` pass.
- [ ] CI is green on `main`.
- [ ] `grep -rn "TODO(phase-" backend frontend` lists the full work list of all phases.
- [ ] The README setup takes a new student less than 30 minutes.
- [ ] `.env.example` has every variable. No secret is in Git.
- [ ] Tag the commit: `git tag phase-0-complete`.

## 0.6 Change Control After Handover

| Change | Who | How |
|---|---|---|
| Schema change | Instructor | New Alembic migration on `main`. Students merge `main` into their branch. |
| Pydantic schema or API change | Instructor | Update §18 of the design document and the schemas. Announce it. |
| Bug in the skeleton | Student reports. Instructor fixes. | Issue on GitHub. |
| New dependency | Student proposes. Instructor approves. | Pull request. |

## 0.7 Common Problems in Phase 0

| Problem | Cause | Fix |
|---|---|---|
| `alembic check` shows differences after autogenerate | Index with `DESC`, identity column or `server_default` text differ | Edit the migration by hand. Compare with §7.1. |
| Tests fail with "database does not exist" | The database was not created | `psql -U postgres -c "CREATE DATABASE socratic_agent OWNER postgres"`. |
| `create_admin.py` fails on import | `passwords.py` is still a stub | Implement `hash_password` (Step 5 note). |
| `/docs` is missing endpoints | A router is not included in `router.py` | Include all routers. |
| Savepoint errors in tests | SQLAlchemy older than 2.0 | Use SQLAlchemy 2.x (`join_transaction_mode`). |
