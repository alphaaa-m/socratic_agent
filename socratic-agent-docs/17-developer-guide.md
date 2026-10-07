# Developer Guide

*Socratic Agent project document. [Index](README.md) | [← Previous](16-roadmap-mvp-future.md) | [Next →](18-consistency-check.md)*

---

## 32. Developer Guide

### 32.1 Prerequisites

| Tool | Version |
|---|---|
| Git | Current |
| Python | 3.12 or newer |
| `uv` | Current (Python package manager, replaces `pip`) |
| Node.js | 20 LTS or newer |
| Local PostgreSQL | 15 or newer (no Docker) |
| A Groq or Gemini API key | - |

### 32.2 Repository Layout

```text
socratic-agent/
├── backend/
├── frontend/
├── .github/workflows/ci.yml
├── .gitignore
└── README.md
```

### 32.3 Project Setup

```bash
git clone https://github.com/<your-org>/socratic-agent.git
cd socratic-agent
```

### 32.4 PostgreSQL Setup

Use the local PostgreSQL service (no Docker). Create the single database once:

```bash
psql -U postgres -c "CREATE DATABASE socratic_agent OWNER postgres"
pg_isready -h localhost -p 5432        # must report "accepting connections"
```

### 32.5 Backend Setup

```bash
cd backend
uv venv
uv pip install -r requirements.txt
cp .env.example .env                   # then edit the values
```

Example `.env`:

```text
APP_ENV=local
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/socratic_agent
JWT_SECRET=<output of: openssl rand -hex 32>
CORS_ORIGINS=["http://localhost:3000"]
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=<your key>
RAG_ENABLED=false
```

For Gemini, set `LLM_PROVIDER=gemini`, `LLM_MODEL=<your model name, e.g. gemini-2.0-flash>` and `GOOGLE_API_KEY`. For OpenAI/Anthropic, set `LLM_PROVIDER=openai`/`anthropic` with `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`.

### 32.6 Database Migrations

```bash
uv run alembic upgrade head                           # apply all migrations
uv run alembic revision --autogenerate -m "add new column"  # create a migration after a model change
uv run alembic downgrade -1                           # undo the last migration
uv run alembic check                                  # models and migrations must match
uv run python scripts/seed.py                         # sample subjects
uv run python scripts/create_admin.py --email admin@example.com # first administrator (asks for a password)
```

Set `target_metadata = Base.metadata` and import `app.models` in `alembic/env.py`. Read the database URL from `Settings`.

### 32.7 Run the Backend

```bash
uv run uvicorn app.main:app --reload --port 8000
# API docs:  http://localhost:8000/docs
# Health:    http://localhost:8000/api/v1/health
```

### 32.8 Frontend Setup

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app
npx shadcn@latest init
npx shadcn@latest add button card input textarea label form badge progress tabs table dialog \
  alert-dialog alert dropdown-menu select sheet scroll-area skeleton sonner switch separator avatar
npm install @tanstack/react-query react-hook-form zod @hookform/resolvers recharts
echo 'BACKEND_API_URL=http://localhost:8000/api/v1' > .env.local
npm run dev                                              # http://localhost:3000
```

### 32.9 RAG Setup (Release 1.1)

```bash
# backend/.env
RAG_ENABLED=true
FAISS_INDEX_DIR=./data/faiss
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

1. Start the backend. The first start downloads the embedding model.
2. Log in as the administrator. Open **Admin → Documents**.
3. Upload a PDF, TXT or MD file for a subject. Wait for the status `indexed`.
4. Use the **Retrieval tester** to check that a query returns the expected chunks.
5. Start a tutoring session in the same subject. The agent messages now have `retrieved_chunk_ids`.
6. To rebuild the index: `python scripts/reindex.py --all`.

The index files are in `FAISS_INDEX_DIR` (one `<subject_id>.faiss` file for each subject). Delete the folder and run `python scripts/reindex.py --all` to rebuild it from PostgreSQL.

### 32.10 Run Both Applications

| Terminal | Command |
|---|---|
| 1 | Ensure local PostgreSQL is running (`pg_isready -h localhost -p 5432`) |
| 2 | `cd backend && uv run uvicorn app.main:app --reload` |
| 3 | `cd frontend && npm run dev` |

Open `http://localhost:3000`, register, then promote your user with `create_admin.py` if you need the admin screens.

### 32.11 Testing

```bash
# Backend
cd backend
uv run pytest -q                               # all tests (needs local PostgreSQL, single DB)
uv run pytest tests/unit -q                    # fast tests only
uv run pytest --cov=app --cov-report=term-missing
uv run ruff check . && uv run ruff format --check .

# Frontend
cd frontend
npm run lint && npx tsc --noEmit
npm test                                    # Vitest
npx playwright test                         # E2E (start the test stack first)

# AI evaluation (live model, costs money)
cd backend && python -m tests.ai.run_eval --set core --report out/eval.md
```

### 32.12 Coding Rules

| Rule | Detail |
|---|---|
| Branching | `main` is protected. Use short-lived branches `feature/<name>`. Open a pull request for each change. |
| Commits | Short imperative subject (for example, "Add hint endpoint"). One logical change for each commit. |
| Pull request checklist | Tests added. Migration included for model changes. API docs and Section 18 updated for endpoint changes. No secrets. CI green. |
| Layering | Follow Section 19.2. The agent must not import SQLAlchemy. Routers must not contain business logic. |
| LLM calls | Only through `LLMGateway`. Never call a provider SDK from a service. |
| Prompts | Keep prompt text in `app/agents/prompts/`. Change a prompt only with an evaluation run. |
| Types | Type hints on all Python functions. `strict` TypeScript. |
| Logging | Log IDs and metrics. Never log secrets or full message text. |

### 32.13 Deployment

Follow Section 28.7. In short: push to `main`. CI runs. Vercel and the backend platform deploy. The pre-deploy command runs `alembic upgrade head`. Run the smoke test.

### 32.14 Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `401 TOKEN_EXPIRED` in a loop | System clock differs, or the refresh cookie is missing | Check the time. Log in again. |
| `psycopg` cannot connect | PostgreSQL is not running or `DATABASE_URL` is wrong | Check the service with `pg_isready -h localhost -p 5432`. Check the URL. |
| `alembic check` shows differences | A model changed without a migration | Create and review a migration. |
| `503 LLM_UNAVAILABLE` | Wrong or missing API key, provider outage, rate limit | Check the key and the provider status. Check the logs for the provider error. |
| Agent output fails schema validation often | The model does not support structured output well | Use a stronger model. Lower the temperature. Check the prompt. |
| Retrieval returns nothing | `RAG_ENABLED=false`, wrong subject, threshold too high, document `failed` | Check the flag, subject and document status. Lower `RAG_MIN_SCORE` for a test. |
| Retrieval returns nothing after a deploy | The index folder is not on the persistent volume, or the index file is missing | Check the volume mount for `FAISS_INDEX_DIR`. Run `python scripts/reindex.py --all`. |
| CORS error in the browser | The browser calls the backend directly | Call `/api/proxy/...` (BFF) instead. Check `CORS_ORIGINS`. |

---

*[Index](README.md) | [← Previous](16-roadmap-mvp-future.md) | [Next →](18-consistency-check.md)*
