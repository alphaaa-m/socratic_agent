# Phase 2: Subjects and Sessions — Windows Test Guide

This guide tests the Phase 2 student and administrator workflows without deleting or resetting the local database. Run each command in the VS Code **PowerShell** terminal unless the guide says otherwise.

## 1. Check prerequisites

Open the repository in VS Code, then open **Terminal > New Terminal**. This checkout is located at:

```powershell
cd C:\Users\User\Desktop\Socratic_Agent\socratic_agent
```

Check the installed tools:

```powershell
py --version
uv --version
node --version
npm.cmd --version
pg_isready --version
psql --version
```

The project requires Python 3.12 or newer, Node.js 20 or newer, `uv`, and PostgreSQL 15 or newer. If `pg_isready` or `psql` is not found, PostgreSQL may be installed but its `bin` folder is not in `PATH`; use the full path to its executable or add that folder to `PATH`.

Use `npm.cmd`, not `npm`, in PowerShell. Some Windows installations block `npm.ps1` because of the PowerShell execution policy; `npm.cmd` avoids changing that policy.

## 2. Prepare the backend safely

In the terminal, open the backend folder:

```powershell
cd C:\Users\User\Desktop\Socratic_Agent\socratic_agent\backend
```

Create the virtual environment and install packages if they are not already present:

```powershell
uv venv
uv pip install -r requirements.txt
```

You do not need to activate the environment when using `uv run`. If you prefer to activate it for ordinary Python commands, use:

```powershell
.\.venv\Scripts\Activate.ps1
```

Create a local settings file only when it is missing:

```powershell
Copy-Item .env.example .env
```

Do **not** paste `.env` contents into chat, source control, screenshots, or commits. Update `DATABASE_URL` with your own local PostgreSQL credentials and replace `JWT_SECRET` with a secret of at least 32 bytes. This creates a suitable value:

```powershell
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

The repository example targets the local `socratic_agent` database. Keep its database name unless you intentionally configured a different local database.

## 3. Start PostgreSQL and prepare existing data

First verify the PostgreSQL service and connection:

```powershell
pg_isready -h localhost -p 5432
psql -U postgres -d socratic_agent -c "SELECT current_database(), current_user;"
```

The first command should say `accepting connections`. If the database has never been created, create it once:

```powershell
psql -U postgres -c "CREATE DATABASE socratic_agent OWNER postgres"
```

If PostgreSQL reports that it already exists, that is fine. Never drop, recreate, or reset the database for this guide.

Apply the existing migration safely from the **backend** folder:

```powershell
uv run alembic upgrade head
```

Seed the normal subjects:

```powershell
uv run python scripts/seed.py
```

`seed.py` checks subject names before adding rows, so it can be re-run without duplicating the three supplied subjects. To inspect them instead of changing anything, use this read-only query:

```powershell
psql -U postgres -d socratic_agent -c "SELECT id, name, is_active FROM subjects ORDER BY name;"
```

For administrator browser and Swagger checks, create or promote an administrator with the provided interactive script:

```powershell
uv run python scripts/create_admin.py --email admin@example.com --name "Local Administrator"
```

Choose your own email and password. The project does not supply a seeded administrator account or password.

## 4. Start the backend and frontend

From the **backend** folder, start the API:

```powershell
uv run uvicorn app.main:app --reload
```

Leave that terminal running. Open [Swagger UI](http://localhost:8000/docs) and confirm the health endpoint responds at `http://localhost:8000/api/v1/health`.

Open a second VS Code PowerShell terminal and run:

```powershell
cd C:\Users\User\Desktop\Socratic_Agent\socratic_agent\frontend
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

If `.env.local` already exists, keep it and verify that `BACKEND_API_URL=http://localhost:8000/api/v1` is appropriate for your backend. Do not put tokens or secrets in this frontend file.

Next.js prints the actual local URL when it starts. It is normally `http://localhost:3000`; if that port is busy, use the alternate local URL printed in the terminal instead.

## 5. Run automated checks

Run backend commands from `socratic_agent\backend`:

```powershell
uv run pytest tests/phase_2 -q
uv run pytest -q
uv run ruff check .
uv run python -m compileall app
```

The focused command runs the Phase 2 subjects, sessions, and administrator tests. The full suite also checks the earlier authentication work. Tests use the configured local database, create a transaction for each test, and roll it back; they do not drop or recreate your database.

Run frontend commands from `socratic_agent\frontend`:

```powershell
npm.cmd test
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

`npm.cmd test` runs Vitest, including the Phase 2 subject-start, filter, and admin-navigation checks. `typecheck` runs TypeScript without writing output. `lint` is the existing Next.js lint command. `build` is the production build.

Expected result: each successful command ends with exit code `0`. Pytest and Vitest report their number of passing tests. If a command fails, record its exact output before changing code; see troubleshooting below.

## 6. Swagger API walkthrough

Swagger sends requests directly to the backend, so first obtain an access token.

1. Use `POST /api/v1/auth/register` to create a student with your own name, email, and a password of 8–128 characters containing a letter and digit. It returns only account data.
2. Use `POST /api/v1/auth/login` with that student’s credentials. Copy **only** `access_token` temporarily.
3. Click **Authorize** at the top of Swagger and enter `Bearer ` followed by the access token. Do not save or share it.

Test student APIs in this order:

1. `GET /api/v1/subjects` returns active subjects, sorted by name.
2. `GET /api/v1/subjects?active_only=false` also returns retired subjects.
3. Copy a subject `id` and use `POST /api/v1/sessions` with:

   ```json
   { "subject_id": "the-subject-uuid" }
   ```

   Expect `201`, `status: "active"`, and `ended_at: null`.
4. Use `GET /api/v1/sessions`, then try `subject_id`, `status`, `limit`, and `offset` query parameters. The response has `items`, `total`, `limit`, and `offset`.
5. Copy a session ID and call `GET /api/v1/sessions/{session_id}`. It returns state and summary fields, but not messages.

For administrator APIs, log in with the account created by `scripts/create_admin.py`, authorize with its access token, then:

1. Use `POST /api/v1/subjects` with a unique name and optional description. Expect `201`.
2. Use `PATCH /api/v1/subjects/{subject_id}` to rename it, change its description, or send `{ "is_active": false }` to retire it. Expect `200`.
3. Retired subjects are absent from the normal `GET /subjects` response, but appear with `active_only=false`.
4. Use `DELETE /api/v1/subjects/{subject_id}` only for an empty test subject. Expect `204`. A subject with sessions or documents returns `409`; retire it instead.
5. Use `GET /api/v1/users?role=student&q=part-of-a-name-or-email&limit=20&offset=0` to list accounts. Password hashes and tokens are never returned.
6. Use `PATCH /api/v1/users/{user_id}` with `{ "role": "admin" }` or `{ "is_active": false }`. Try changing your own administrator role or active state to confirm the expected `400` protection.

## 7. Browser walkthrough

### Student

1. Open the frontend URL, choose **Create an account**, register, then sign in.
2. On the dashboard, choose **Start new session** or open **Subjects** in the sidebar.
3. Confirm that only active subjects appear as cards. Click **Start session** once.
4. You should be taken to `/sessions/<id>`, which shows the safe Phase 3 chat placeholder rather than a chat implementation.
5. Return to **Dashboard**: the new session appears in the five most recent entries.
6. Open **Session history**. Test the subject/status filters and page controls. Only the signed-in user’s sessions should be listed.

### Administrator

1. Sign out and sign in with the administrator account you created.
2. The sidebar now shows the **Admin** group.
3. Open **Admin > Subjects**. Create a unique subject, edit it, then retire it. Sign in as a student again and confirm the retired subject no longer appears under **Subjects**.
4. Open **Admin > Users**. Search and filter users, change another user’s role or active status, and verify an attempt to demote or deactivate the current administrator shows the backend error.

The UI hides administrator controls for students, but the backend remains authoritative: a student calling those API endpoints receives `403`.

## 8. Safe database verification

These commands are read-only. Replace `YOUR_EMAIL` with the student email you used. Run them from any terminal that can use `psql`:

```powershell
psql -U postgres -d socratic_agent -c "SELECT s.id, s.status, s.started_at, s.ended_at, s.agent_state FROM learning_sessions s JOIN users u ON u.id = s.user_id WHERE u.email = 'YOUR_EMAIL' ORDER BY s.started_at DESC;"
psql -U postgres -d socratic_agent -c "SELECT u.email, p.current_level, p.total_sessions FROM learner_profiles p JOIN users u ON u.id = p.user_id WHERE u.email = 'YOUR_EMAIL';"
psql -U postgres -d socratic_agent -c "SELECT u.email, sub.name, lp.topics_attempted, lp.topics_mastered FROM learning_progress lp JOIN users u ON u.id = lp.user_id JOIN subjects sub ON sub.id = lp.subject_id WHERE u.email = 'YOUR_EMAIL' ORDER BY sub.name;"
```

After each started session, expect one `learning_sessions` row with `status = active`, `ended_at` empty, and an `agent_state` difficulty of 2, 3, or 4 based on the learner level. `total_sessions` and the matching `topics_attempted` each increase by one.

To verify ownership, use two student accounts. Start a session as the first student, sign in through Swagger as the second student, and request the first session ID with `GET /api/v1/sessions/{session_id}`. The expected result is `404`, not `403`, and the session’s data is not revealed.

## 9. Troubleshooting

- **PostgreSQL connection fails:** Start the PostgreSQL Windows service, run `pg_isready`, and check the host, port, database, username, and password in `backend\.env`.
- **`database "socratic_agent" does not exist`:** Create it once with the command in section 3, then run `uv run alembic upgrade head`. Do not drop any existing database.
- **Port 8000 or 3000 is in use:** Stop the existing development server if it is yours, or use the alternate frontend URL Next.js prints. For the API, start Uvicorn on a chosen free port and update `frontend\.env.local` to the matching `/api/v1` URL.
- **Swagger returns `401` or `403`:** Log in again, use a fresh access token in **Authorize**, and confirm the account is active. Administrator routes additionally require a database role of `admin`.
- **The browser shows a frontend API error:** Confirm the backend terminal is still running, `BACKEND_API_URL` in `.env.local` has `/api/v1`, and reload after signing in again.
- **No subjects are shown:** Run the idempotent `uv run python scripts/seed.py`, then refresh. Retired subjects intentionally do not appear to students.
- **Tests fail before running:** Install the dependencies in the matching `backend` or `frontend` folder. Read the exact first error; it often identifies a missing database connection or package.
- **PowerShell says `npm` scripts are disabled:** run `npm.cmd` as shown; no execution-policy change is necessary.
- **Production build runs out of memory:** close other memory-heavy programs and retry `npm.cmd run build` in a normal terminal with enough available memory. This does not change application data.

Finally, before committing any work, run `git status`. `.env`, `.env.local`, access tokens, database passwords, and other secrets must never be committed.
