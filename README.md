# Socratic Agent

AI-powered tutoring through guided questioning (docs in `socratic-agent-docs/` and `implementation-guide/`).

## Prerequisites

- Python 3.12+, `uv`, Node.js 20+, local PostgreSQL 15+ (no Docker)

## Setup

```bash
# 1. Database (single DB): create once
psql -U postgres -c "CREATE DATABASE socratic_agent OWNER postgres"

# 2. Backend
cd backend
uv venv
uv pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL / JWT_SECRET / LLM keys (already filled for local dev)
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn app.main:app --reload  # http://localhost:8000/docs, health: /api/v1/health

# 3. Frontend
cd ../frontend
npm install && npm run dev  # http://localhost:3000
```

Single local DB: `postgresql://postgres:postgres123@localhost:5432/socratic_agent`.
Tests run against the same DB (savepoint rollback per test, schema ensured via `alembic upgrade head` — never dropped).

## LLM providers

Phase 0-3 use `LLM_PROVIDER=fake` (deterministic `FakeGateway`).
From Phase 4, set `LLM_PROVIDER=groq` (`GROQ_API_KEY`, model e.g. `llama-3.3-70b-versatile`)
or `LLM_PROVIDER=gemini` (`GOOGLE_API_KEY`, model e.g. `gemini-2.0-flash`).
Embeddings (Phase 7) use HuggingFace `sentence-transformers` (see `EMBEDDING_MODEL`).

## RAG storage split

- PostgreSQL `document_chunks`: chunk **text**, order (`chunk_index`), metadata — the source of truth.
- FAISS: only embedding **vectors**, keyed by `document_chunks.vector_id` (`GENERATED ALWAYS AS IDENTITY`).
- Retrieval = FAISS top-K `vector_id`s → Postgres lookup of the chunk text. Rebuild the index anytime from Postgres.

## Find work

```bash
grep -rn "TODO(phase-" backend/app frontend/app frontend/components
```

## Rules (summary)

- Routers call services; services own DB transactions; agent never imports SQLAlchemy.
- LLM only through `LLMGateway` (fake provider until Phase 4).
- One transaction per turn; no DB connection held during LLM calls.
- Never commit secrets (only `.env.example`).
