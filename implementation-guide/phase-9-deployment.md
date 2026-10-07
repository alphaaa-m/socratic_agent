# Phase 9: Deployment (Student)

*[Index](README.md) | [← Phase 8](phase-8-testing-and-evaluation.md)*

**Owner:** Student (with the instructor for accounts and billing). **Time:** about 1 week. **Branch:** `phase-9/<your-name>`.

## 9.1 Goal

The system runs in production: Next.js on Vercel, FastAPI on Railway or Render, managed PostgreSQL, and a FAISS index on a persistent volume. Migrations run on deploy. A smoke test passes. The instructor can open a public link and use the system.

## 9.2 Read First

| Topic | Design section |
|---|---|
| Deployment | §28 (all) |
| Environment variables | §28.3 |
| Migrations | §28.5 |
| FAISS operation | §28.6 |
| Security | §26 (API security, environment variables, LLM key protection) |
| Developer guide | §32.13, §32.14 (troubleshooting) |

## 9.3 Before You Start

Ask the instructor for:

- [ ] The GitHub repository access (admin rights to connect Vercel and the backend host).
- [ ] An account on Vercel and on Railway or Render.
- [ ] A **production** LLM API key (not your personal key) with a monthly spending limit.
- [ ] A decision: Railway or Render (one only).

## 9.4 Your Work List

| # | Task | Where | Notes |
|---|---|---|---|
| 1 | Backend start command | host dashboard | From §28.4: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` (no Docker). Install the **CPU** build of PyTorch for the RAG dependencies. Run one worker (`--workers 1`). Use `${PORT}`. |
| 2 | Local service test | terminal | Run the backend with `uv run uvicorn ...` and a `.env` file. `/api/v1/health` must work. |
| 3 | Production settings | `core/config.py` (check) | `APP_ENV=production` disables `/docs`. CORS only for the Vercel domain. Check that the `DATABASE_URL` converter works for the host's URL format. |
| 4 | Managed database | host dashboard | Create PostgreSQL. Copy the connection URL. Check that backups are on. |
| 5 | Backend service | host dashboard | Deploy from GitHub (root `backend`, start command from task 1, no Dockerfile). Add a **persistent volume** at `/data`. Set the variables of §28.3 (`FAISS_INDEX_DIR=/data/faiss`, `RAG_ENABLED` as the instructor decides, secrets as secrets). |
| 6 | Pre-deploy migration | host dashboard | Pre-deploy or release command: `alembic upgrade head`. Health check path: `/api/v1/health`. |
| 7 | First data | host shell | `python scripts/seed.py`, then `python scripts/create_admin.py --email <instructor email>`. |
| 8 | Frontend project | Vercel | Import the repository (root `frontend`). Set `BACKEND_API_URL` (server-side only, no `NEXT_PUBLIC_` prefix). Deploy. |
| 9 | CORS check | backend variables | Add the Vercel URL to `CORS_ORIGINS`. Redeploy the backend. |
| 10 | Cookie check | browser | In production the cookies must have `Secure` and `httpOnly`. Fix the BFF if the `Secure` flag is missing. |
| 11 | CI/CD | `.github/workflows/ci.yml` | Deploy only after CI passes on `main`. Use the host and Vercel Git integration with "wait for CI". |
| 12 | Monitoring | external | Add an uptime monitor for `/api/v1/health` (any free service). Look at the log viewer once for JSON logs with `request_id`. |
| 13 | Spending limit | LLM provider console | Confirm the monthly limit and an alert. |
| 14 | Smoke test | `docs/smoke-test.md` | Write the checklist (below) and run it on production. |
| 15 | Rollback test | hosts | Practice once: promote the previous Vercel deployment, and redeploy the previous backend commit. Write the steps in `docs/rollback.md`. |
| 16 | Runbook | `docs/runbook.md` | One page: where the logs are, how to restart, how to rebuild the FAISS index (`reindex.py`), how to rotate the JWT secret and the LLM key, who to call. |

## 9.5 Environment Variables Checklist

Backend (set in the host, never in Git):

| Variable | Done |
|---|---|
| `APP_ENV=production` | ☐ |
| `DATABASE_URL` | ☐ |
| `JWT_SECRET` (32 bytes or more, `openssl rand -hex 32`) | ☐ |
| `CORS_ORIGINS` (JSON list with the Vercel URL) | ☐ |
| `LLM_PROVIDER`, `LLM_MODEL`, the provider API key | ☐ |
| `RAG_ENABLED`, `FAISS_INDEX_DIR=/data/faiss`, `EMBEDDING_MODEL` | ☐ |
| `RAG_TOP_K`, `RAG_MIN_SCORE`, `MAX_UPLOAD_MB`, `MESSAGES_PER_MINUTE` | ☐ |
| `ALLOW_FINAL_REVEAL=false` | ☐ |

Frontend (Vercel):

| Variable | Done |
|---|---|
| `BACKEND_API_URL` (server-side) | ☐ |

## 9.6 Smoke Test (Run on Production)

1. Open the Vercel URL. The login page loads over HTTPS.
2. Register a new student. Log in.
3. Open the subject list. Start a session.
4. Send a first question. A guiding question arrives within 8 seconds.
5. Send an answer. Feedback and the status bar update.
6. Press the hint button.
7. Reach the answer (or end the session). Read the summary.
8. Open the progress page and the history page.
9. Log out. Open `/dashboard` directly. The app goes to `/login`.
10. Log in as the administrator. Open the admin pages.
11. If `RAG_ENABLED=true`: upload a small document, wait for `indexed`, use the retrieval tester, and run a session in that subject.
12. Open `/api/v1/health` on the backend: `status` is `ok`.
13. Open `/docs` on the backend: it must **not** be available in production.
14. Redeploy the backend. Check that the FAISS index is still there (retrieval still works) and the database data is unchanged.

## 9.7 Hints

- The first request after a deploy can be slow because the embedding model loads. Load it at startup (lifespan), not on the first request.
- If the host gives a `postgres://` URL, the settings converter must handle it (it is in §19.3).
- If login works but the next request returns `401`, check the cookie settings (`Secure`, `SameSite`, the cookie path) and that the BFF and the browser use the same domain.
- If the backend does not start, read the first error in the host log. It is usually a missing variable.
- Keep `workers` at 1. With FAISS in memory, a second worker would have a stale index (§28.6).
- Never put the production `DATABASE_URL` on your laptop's `.env`. Use the host shell for one-time scripts.

## 9.8 Definition of Done

- [ ] The smoke test passes on production. Results are saved in `docs/smoke-test.md` with the date.
- [ ] `alembic upgrade head` runs automatically on deploy.
- [ ] The index survives a redeploy.
- [ ] The cookies are `httpOnly` and `Secure`. `/docs` is off. CORS allows only the Vercel domain.
- [ ] Secrets exist only in the hosts. A search of the repository finds none.
- [ ] Uptime monitor, spending limit, backups and the runbook exist.
- [ ] The rollback was practiced once.
- [ ] The instructor used the live system.

## 9.9 Demo for the Instructor

1. Open the live URL and complete a short tutoring session.
2. Show the deploy log with the migration step.
3. Show the environment variable names in both hosts (not the values).
4. Redeploy and show that data and the index stay.
5. Show the monitor, the log viewer and the runbook.

## 9.10 Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| `NEXT_PUBLIC_` prefix on `BACKEND_API_URL` | The value goes into the browser bundle. |
| No persistent volume for `/data` | The FAISS index is lost at every deploy. |
| Migration run by hand after the deploy | The new code can start before the schema is ready. Use the pre-deploy command. |
| More than one backend worker or instance | The FAISS index is in memory and written by one process only. |
| Using your personal LLM key | No spending control and a risk if it leaks. |
| Leaving `/docs` open in production | Shows the full API to everyone. |
| Testing only on `localhost` | Cookie, CORS and HTTPS problems appear only in production. |

## 9.11 After Phase 9

Run the full acceptance checklist of §30.3 on the live system. Then tag the release:

```bash
git tag v1.0.0-mvp && git push --tags
```

Possible next steps are in §31 (future enhancements) and §30.4 (Release 1.1 and 1.2).
