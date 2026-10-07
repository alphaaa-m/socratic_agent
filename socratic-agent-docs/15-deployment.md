# Deployment Architecture

*Socratic Agent project document. [Index](README.md) | [← Previous](14-security-and-errors.md) | [Next →](16-roadmap-mvp-future.md)*

---

## 28. Deployment Architecture

### 28.1 Architecture

```text
User
 ↓
Vercel
 ↓
Next.js
 ↓
FastAPI on Railway / Render
 ↓
PostgreSQL
 ↓
LLM API
 ↓
FAISS Index
```

```mermaid
flowchart LR
    U([User browser]) -->|HTTPS| V[Vercel<br/>Next.js UI + BFF]
    V -->|HTTPS, Bearer JWT| F[FastAPI<br/>Railway or Render]
    F -->|TLS| P[(Managed PostgreSQL)]
    F -->|HTTPS| L[(LLM API)]
    F -->|local volume| C[(FAISS index)]
    G[GitHub] -->|push to main| V
    G -->|push to main| F
```

### 28.2 Services

| Service | Platform | Notes |
|---|---|---|
| Frontend | Vercel | Root directory `frontend`. Automatic deploy from GitHub. Preview deploys for pull requests. |
| Backend | Railway or Render | Direct `uv run uvicorn` service from `backend/` (no Docker). Health check `/api/v1/health`. |
| Database | Managed PostgreSQL (Railway, Render or other) | Automatic backups. TLS. Private network where possible. |
| Vector store | FAISS index files on a persistent volume of the backend service | Mount at `/data`. See 28.6 for scaling limits. |
| LLM | Groq or Gemini API (OpenAI/Anthropic also supported) | Key in backend environment. |

### 28.3 Environment Variables

**Backend (`backend/.env.example`)**

| Variable | Example | Description |
|---|---|---|
| `APP_ENV` | `production` | `local`, `test` or `production`. |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/db` | Provided by the database service. The app converts it to the `psycopg` driver URL. |
| `JWT_SECRET` | (random, 32 bytes or more) | Generate with `openssl rand -hex 32`. |
| `ACCESS_TOKEN_MINUTES` / `REFRESH_TOKEN_DAYS` | `30` / `7` | Token lifetimes. |
| `CORS_ORIGINS` | `["https://your-app.vercel.app"]` | JSON list of allowed origins. |
| `LLM_PROVIDER` | `groq`, `gemini` (`openai`, `anthropic` also supported) | Provider selection. |
| `LLM_MODEL` | (your model name, e.g. `llama-3.3-70b-versatile`, `gemini-2.0-flash`) | Model for the provider. |
| `GROQ_API_KEY` / `GOOGLE_API_KEY` | (secret) | Set the one that you use (`GOOGLE_API_KEY` for Gemini). |
| `LLM_TIMEOUT_SECONDS` / `LLM_MAX_RETRIES` | `30` / `2` | LLM call limits. |
| `RAG_ENABLED` | `false` for MVP | Feature flag. |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Changing it needs a full re-index. |
| `FAISS_INDEX_DIR` | `/data/faiss` | Folder for the FAISS index files (one file for each subject). Must be on the persistent volume. |
| `RAG_TOP_K` / `RAG_MIN_SCORE` | `4` / `0.35` | Retrieval settings. |
| `MAX_UPLOAD_MB` | `10` | Upload limit. |
| `MESSAGES_PER_MINUTE` | `20` | Rate limit for messages. |
| `ALLOW_FINAL_REVEAL` | `false` | Keep `false`. |

**Frontend (Vercel project settings)**

| Variable | Example | Description |
|---|---|---|
| `BACKEND_API_URL` | `https://socratic-api.up.railway.app/api/v1` | Server-side only. Used by the BFF. Do not use the `NEXT_PUBLIC_` prefix. |
| `NEXT_PUBLIC_APP_NAME` | `Socratic Agent` | Optional public value. |

### 28.4 Production Configuration

- Run `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` (no Docker; `uv sync` or `uv pip install -r requirements.txt` first). The FAISS index lives in the memory of one process, and only that process writes the index files. Use threads for concurrency (Section 28.6).
- Set `APP_ENV=production` (this disables `/docs`).
- Use a connection pool (`pool_size=5`, `max_overflow=5`, `pool_pre_ping=True`). Keep the total below the database connection limit.
- Set the LLM spending limit at the provider.
- Enable JSON logs and send them to the platform log viewer.
- Add an uptime monitor for `/api/v1/health`.
- For the RAG dependencies, install the CPU build of PyTorch to keep the environment small: `uv pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt`.

### 28.5 Database Migration

1. Write the model change.
2. Run `alembic revision --autogenerate -m "description"` locally.
3. Read the generated file. Fix it by hand if necessary (triggers and extensions are not auto-detected).
4. Run `alembic upgrade head` on a local database. Run `alembic downgrade -1` and `alembic upgrade head` again.
5. Commit the migration with the code.
6. On deploy, run `alembic upgrade head` **before** the new application version takes traffic. Use the release or pre-deploy command of the platform (for example, Railway "pre-deploy command" or Render "pre-deploy command").
7. Make migrations backward compatible for one release: add columns as nullable or with a default; remove columns in a later release.

### 28.6 Vector Store Operation and Scaling

| Topic | Rule |
|---|---|
| Persistence | The volume at `/data` must persist across deploys. Without a volume, the index is lost. The system can rebuild it with `scripts/reindex.py --all`. |
| Single writer | The FAISS index is loaded into the memory of the backend process. Only one process must write the index files. Use `--workers 1` and one instance. |
| Scale-out | When you need more than one backend instance, move the index to a dedicated retrieval service (one writer, many readers) or use `pgvector` in PostgreSQL (future change behind the `VectorStore` interface). |
| Index type | `IndexFlatIP` (exact search) in an `IndexIDMap2`. It handles about 100,000 chunks with low latency. For larger collections, change to an IVF or HNSW index inside `FaissVectorStore`. |
| Backup | Back up the volume daily, or rely on re-indexing from PostgreSQL. |

### 28.7 Deployment Steps

| Step | Action |
|---|---|
| 1 | Create the managed PostgreSQL database. Copy `DATABASE_URL`. |
| 2 | Create the backend service from the GitHub repository (root `backend`, start command `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`). Add a persistent volume at `/data`. |
| 3 | Set all backend environment variables (28.3). |
| 4 | Set the pre-deploy command to `alembic upgrade head`. Set the health check path to `/api/v1/health`. |
| 5 | Deploy the backend. Check `/api/v1/health` returns `ok`. |
| 6 | Run `python scripts/seed.py` (sample subjects) and `python scripts/create_admin.py` (first administrator) once, with the platform shell. |
| 7 | Import the frontend project in Vercel (root `frontend`). Set `BACKEND_API_URL`. Deploy. |
| 8 | Add the Vercel domain to `CORS_ORIGINS` (needed for direct browser calls and tools; the BFF does not need CORS). Redeploy the backend. |
| 9 | Run the smoke test: register, log in, start a session, send a message, end the session, open the progress page. |
| 10 | Turn on monitoring and alerts. Check the LLM spending limit. |
| 11 | (Release 1.1) Set `RAG_ENABLED=true`. Upload documents. Test retrieval in the admin screen. |

### 28.8 CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: postgresql://postgres:postgres123@localhost:5432/socratic_agent
      JWT_SECRET: test-secret-test-secret-test-secret-12
      LLM_PROVIDER: fake
      LLM_MODEL: fake
      APP_ENV: test
    defaults: { run: { working-directory: backend } }
    steps:
      - uses: actions/checkout@v4
      - name: Install PostgreSQL (no Docker)
        run: |
          sudo apt-get update -y
          sudo apt-get install -y postgresql postgresql-contrib
          sudo service postgresql start
          sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres123';"
          sudo -u postgres createdb socratic_agent
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - uses: astral-sh/setup-uv@v4
      - run: uv pip install --system -r requirements.txt
      - run: ruff check .
      - run: alembic upgrade head && alembic check
      - run: pytest -q
  frontend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: frontend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm, cache-dependency-path: frontend/package-lock.json }
      - run: npm ci
      - run: npm run lint && npx tsc --noEmit && npm test
      - run: npm run build
```

### 28.9 Rollback

- Frontend: promote a previous deployment in Vercel.
- Backend: redeploy the previous commit (start command unchanged). If a migration ran, use the backward-compatible rule (28.5). Run `alembic downgrade` only after a test on a copy of the data.
- Database: restore from the latest backup (point-in-time recovery if the provider supports it).

---

*[Index](README.md) | [← Previous](14-security-and-errors.md) | [Next →](16-roadmap-mvp-future.md)*
