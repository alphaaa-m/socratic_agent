# Socratic Agent

AI-powered tutoring through guided questioning (docs in `socratic-agent-docs/` and `implementation-guide/`).

## Prerequisites

- Python 3.12+, Node.js 20+, PostgreSQL 15+ (local service or `docker compose up -d db`)

## Setup

```bash
# 1. Database (native Postgres): create DBs
psql -U postgres -c "CREATE DATABASE socratic_agent OWNER postgres"
psql -U postgres -c "CREATE DATABASE socratic_agent_test OWNER postgres"

# 2. Backend
cd backend
py -3.13 -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL / JWT_SECRET (already filled for local dev)
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload  # http://localhost:8000/docs, health: /api/v1/health

# 3. Frontend
cd ../frontend
npm install && npm run dev  # http://localhost:3000
```

Default local DB: `postgresql://postgres:postgres123@localhost:5432/socratic_agent`
(test DB: `.../socratic_agent_test`).

## Find work

```bash
grep -rn "TODO(phase-" backend/app frontend/app frontend/components
```

## Rules (summary)

- Routers call services; services own DB transactions; agent never imports SQLAlchemy.
- LLM only through `LLMGateway` (fake provider until Phase 4).
- One transaction per turn; no DB connection held during LLM calls.
- Never commit secrets (only `.env.example`).
