# FastAPI Backend Architecture

*Socratic Agent project document. [Index](README.md) | [← Previous](09-api.md) | [Next →](11-frontend-and-ui.md)*

---

## 19. FastAPI Backend Architecture

### 19.1 Directory Structure

```text
backend/
├── app/
│   ├── main.py                      # app factory, middleware, routers, lifespan
│   ├── api/
│   │   ├── deps.py                  # get_db, get_current_user, require_admin
│   │   └── v1/
│   │       ├── router.py            # includes all routers under /api/v1
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── subjects.py
│   │       ├── sessions.py
│   │       ├── messages.py
│   │       ├── assessments.py
│   │       ├── progress.py
│   │       ├── documents.py
│   │       └── health.py
│   ├── models/                      # SQLAlchemy ORM models (Section 7.2)
│   │   ├── enums.py  user.py  learner_profile.py  subject.py  learning_session.py
│   │   └── message.py  learner_assessment.py  learning_progress.py
│   │       knowledge_document.py  document_chunk.py
│   ├── schemas/                     # Pydantic request and response models
│   │   ├── common.py  auth.py  user.py  subject.py  session.py
│   │   └── message.py  assessment.py  progress.py  document.py
│   ├── services/                    # business logic and transactions
│   │   ├── auth_service.py  user_service.py  subject_service.py
│   │   ├── session_service.py  tutoring_service.py  assessment_service.py
│   │   └── progress_service.py  document_service.py
│   ├── agents/                      # the single Socratic Agent
│   │   ├── socratic_agent.py        # facade: handle_turn, summarize
│   │   ├── schemas.py               # AgentState, EvaluationResult, TutorReply ...
│   │   ├── llm_gateway.py           # LLMGateway protocol + LangChainGateway
│   │   ├── llm_factory.py           # build_chat_model (OpenAI, Anthropic, Ollama)
│   │   ├── capabilities/
│   │   │   ├── dialogue_engine.py   # incl. answer-leak guard
│   │   │   ├── level_estimator.py
│   │   │   ├── response_evaluator.py
│   │   │   ├── adaptive_controller.py
│   │   │   ├── hint_generator.py
│   │   │   ├── conversation_memory.py
│   │   │   ├── knowledge_retriever.py   # thin wrapper over app/rag retriever
│   │   │   ├── prompt_builder.py
│   │   │   ├── misconception_detector.py
│   │   │   └── session_summarizer.py
│   │   └── prompts/                 # system prompt, templates, mode texts
│   ├── rag/
│   │   ├── embeddings.py  chunking.py  loaders.py  ingestion.py
│   │   ├── vector_store.py          # VectorStore protocol
│   │   ├── vector_store_faiss.py    # FaissVectorStore (one index file per subject)
│   │   └── retriever.py             # KnowledgeRetriever, NullRetriever
│   ├── database/
│   │   ├── base.py                  # Base, naming convention, mixins
│   │   └── session.py               # engine, SessionLocal, get_db
│   ├── auth/
│   │   ├── jwt.py                   # create_token, decode_token
│   │   └── passwords.py             # Argon2 hash and verify
│   └── core/
│       ├── config.py                # Settings (pydantic-settings)
│       ├── exceptions.py            # AppError subclasses + handlers
│       ├── logging.py               # JSON logging, request ID
│       └── rate_limit.py            # slowapi limiter
├── alembic/                         # migrations (env.py, versions/)
├── alembic.ini
├── scripts/                         # seed.py, create_admin.py, reindex.py
├── tests/
│   ├── conftest.py
│   ├── unit/  api/  db/  integration/  rag/  ai/
├── Dockerfile
├── requirements.txt
└── .env.example
```

### 19.2 Layer Responsibilities

| Layer | Responsibility | Must not |
|---|---|---|
| `api` | Parse HTTP. Validate with Pydantic. Authenticate. Call one service method. Return a schema. | Contain business rules or SQL. |
| `schemas` | Define the JSON contract. | Contain database objects. |
| `services` | Run business rules. Own transactions. Call the agent and RAG. | Know about HTTP objects. |
| `models` | Map tables to Python classes. | Contain business logic. |
| `agents` | Run the Socratic logic. Call the LLM through the gateway. | Access the database or HTTP. |
| `rag` | Ingest documents. Search vectors. | Access the database directly (the service passes data in and out). |
| `database` | Create the engine and sessions. Define the base class. | Contain queries for features. |
| `auth` | Hash passwords. Create and verify tokens. | Load users (the dependency does this). |
| `core` | Settings, errors, logging, rate limit. | Import from `api` or `services`. |

**Dependency direction:** `api → services → (agents, rag, models, database)`. `core` and `auth` are leaf modules.

### 19.3 Settings

```python
# app/core/config.py
from functools import lru_cache
from typing import Literal
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["local", "test", "production"] = "local"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    llm_provider: Literal["openai", "anthropic", "ollama"] = "openai"
    llm_model: str
    llm_temperature: float = 0.3
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    ollama_base_url: str = "http://localhost:11434"

    rag_enabled: bool = False
    faiss_index_dir: str = "./data/faiss"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_top_k: int = 4
    rag_min_score: float = 0.35
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    max_upload_mb: int = 10

    messages_per_minute: int = 20
    allow_final_reveal: bool = False

    @field_validator("database_url")
    @classmethod
    def use_psycopg3(cls, v: str) -> str:
        # Railway and Render give "postgresql://" or "postgres://" URLs.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 19.4 Application Entry Point

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.factory import build_agent
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestIdMiddleware, configure_logging
from app.core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    app.state.agent = build_agent(s)          # builds gateway, retriever, agent once
    yield


def create_app() -> FastAPI:
    s = get_settings()
    configure_logging()
    app = FastAPI(title="Socratic Agent API", version="1.0.0", lifespan=lifespan,
                  docs_url=None if s.app_env == "production" else "/docs")
    app.state.limiter = limiter
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=s.cors_origins, allow_credentials=False,
                       allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])
    register_exception_handlers(app)
    app.include_router(api_router, prefix=s.api_prefix)
    return app


app = create_app()
```

### 19.4.1 Authentication Utilities

```python
# app/auth/passwords.py
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

_hasher = PasswordHasher()                       # Argon2id with library defaults


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False
```

```python
# app/auth/jwt.py
import uuid
from datetime import datetime, timedelta, timezone
import jwt                                        # PyJWT
from app.core.config import get_settings
from app.core.exceptions import UnauthenticatedError


def create_token(user_id, role: str, token_type: str, lifetime: timedelta) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "role": role, "type": token_type,
               "iat": now, "exp": now + lifetime, "jti": uuid.uuid4().hex}
    return jwt.encode(payload, s.jwt_secret.get_secret_value(), algorithm=s.jwt_algorithm)


def decode_token(token: str, expected_type: str) -> dict:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret.get_secret_value(), algorithms=[s.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise UnauthenticatedError(code="TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise UnauthenticatedError(code="TOKEN_INVALID")
    if payload.get("type") != expected_type:
        raise UnauthenticatedError(code="TOKEN_INVALID")
    return payload
```

### 19.5 Tutoring Service (Main Orchestration)

```python
# app/services/tutoring_service.py  (outline)
class TutoringService:
    def __init__(self, db: Session, agent: SocraticAgent, settings: Settings):
        self.db, self.agent, self.settings = db, agent, settings

    def handle_student_message(self, user: User, session_id: UUID, content: str) -> SendMessageResponse:
        # 1. READ PHASE (short transaction)
        ctx = self._load_context(user, session_id)            # session, profile, subject, last 10 messages
        if ctx.session.status != "active":
            raise SessionNotActiveError()
        self.db.rollback()                                    # release the connection before LLM calls

        # 2. AGENT PHASE (no database connection open)
        first = ctx.message_count == 0
        turn = AgentTurnInput(kind="question" if first else "response", student_message=content,
                              subject_id=str(ctx.subject.id), subject_name=ctx.subject.name,
                              subject_description=ctx.subject.description,
                              profile=ctx.profile_snapshot, state=ctx.state,
                              history=ctx.history, is_first_turn=first)
        out = self.agent.handle_turn(turn)

        # 3. WRITE PHASE (one transaction)
        with self.db.begin():
            session = self._lock_session(session_id)          # SELECT ... FOR UPDATE
            if session.agent_state.get("turn_index", 0) != ctx.state.turn_index:
                raise TurnConflictError()
            student_msg = Message(session_id=session.id, sender="student",
                                  message_type=turn.kind, content=content)
            agent_msg = Message(session_id=session.id, sender="agent",
                                message_type=out.reply.message_type, content=out.reply.message,
                                retrieved_chunk_ids=[c.chunk_id for c in out.retrieved])
            self.db.add_all([student_msg, agent_msg]); self.db.flush()
            if out.evaluation:
                self.db.add(LearnerAssessment(session_id=session.id, message_id=student_msg.id,
                            correctness_score=out.evaluation.correctness_score,
                            reasoning_score=out.evaluation.reasoning_score,
                            confidence_score=out.evaluation.confidence_score,
                            difficulty_level=out.difficulty_used,
                            misconception=out.evaluation.misconception,
                            feedback=out.evaluation.feedback,
                            resolves_goal=out.new_state.resolved))
            session.agent_state = out.new_state.model_dump()
            if first:
                session.title = content[:60]
            self._apply_learner_update(user.id, out.learner_update)      # learner_profiles
            self._touch_progress(user.id, session.subject_id)            # last_activity_at
        return self._to_response(student_msg, agent_msg, out, session)
```

`handle_hint_request` follows the same three phases. It uses `kind="hint_request"`, saves only the agent message and the new state, and saves no assessment. `end_session` follows the same pattern (Section 8.1).

### 19.6 Dependencies (`requirements.txt`)

```text
fastapi>=0.110
uvicorn[standard]>=0.29
pydantic>=2.6
pydantic-settings>=2.2
email-validator>=2.1
sqlalchemy>=2.0
alembic>=1.13
psycopg[binary]>=3.1
argon2-cffi>=23.1
PyJWT>=2.8
python-multipart>=0.0.9
slowapi>=0.1.9
tenacity>=8.2
langchain>=0.3
langchain-core>=0.3
langchain-community>=0.3
langchain-openai>=0.2
langchain-anthropic>=0.3
langchain-ollama>=0.2
langchain-huggingface>=0.1
sentence-transformers>=3.0
pypdf>=4.0
faiss-cpu>=1.8
pytest>=8.0
pytest-cov>=5.0
httpx>=0.27
ruff>=0.4
```

---

*[Index](README.md) | [← Previous](09-api.md) | [Next →](11-frontend-and-ui.md)*
