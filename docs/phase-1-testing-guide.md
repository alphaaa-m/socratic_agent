# Phase 1 Authentication: Windows Test Guide

This guide sets up the Phase 1 backend and frontend on Windows, runs the tests, and walks through registration, login, refresh, and logout in a browser.

## 1. Install the tools

Install these programs before starting:

- Python 3.12 (the project CI version) from python.org. Select **Add Python to PATH**.
- Node.js 20 LTS from nodejs.org. This also installs npm.
- PostgreSQL 16 or newer. Remember the password you set for the `postgres` database user, and make sure the PostgreSQL Windows service is running.
- Git, if you have not already downloaded the project.

Open **PowerShell**. The project folder in this checkout is:

```powershell
cd C:\Users\User\Desktop\Socratic_Agent\socratic_agent
```

If you placed the project in another folder, change that path to your own folder. Commands below say which project folder to use.

## 2. Create the local database

In PowerShell, check that PostgreSQL accepts connections:

```powershell
pg_isready -h localhost -p 5432
```

Expected result: `localhost:5432 - accepting connections`.

Create the project database once:

```powershell
psql -U postgres -c "CREATE DATABASE socratic_agent OWNER postgres"
```

If PostgreSQL says the database already exists, leave it in place and continue. Do not drop or reset it.

## 3. Set up and start the backend

In a PowerShell window, go to the **backend folder** and create a virtual environment:

```powershell
cd C:\Users\User\Desktop\Socratic_Agent\socratic_agent\backend
py -3.12 -m venv .venv
```

Install backend packages using the virtual environment's Python. This works without activating the environment, so PowerShell execution-policy settings do not need to change:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create your local settings file and open it in Notepad:

```powershell
Copy-Item .env.example .env
notepad .env
```

In `.env`, set `DATABASE_URL` to your PostgreSQL username, password, host, port, and database. For example, if the `postgres` user's password is `mypassword`:

```text
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/socratic_agent
```

Also replace `JWT_SECRET` with a random value of at least 32 bytes. You can generate 64 hexadecimal characters in PowerShell with:

```powershell
py -3.12 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value after `JWT_SECRET=` in `.env`, save the file, then run the database migration from the **backend folder**:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Start the API in that same PowerShell window:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Keep this window open. The API should be available at `http://localhost:8000`; its interactive API page is `http://localhost:8000/docs`.

## 4. Set up and start the frontend

Open a **second PowerShell window**. Go to the **frontend folder**:

```powershell
cd C:\Users\User\Desktop\Socratic_Agent\socratic_agent\frontend
Copy-Item .env.example .env.local
```

The example file points the Next.js server at `http://localhost:8000/api/v1`. Install packages and start the site:

```powershell
npm.cmd ci
npm.cmd install --no-save --ignore-scripts eslint@8.57.1 eslint-config-next@14.2.35
npm.cmd run dev
```

The second install adds the lint tools used by the existing `next lint` script without changing the saved dependency list. Use `npm.cmd` in PowerShell. On some Windows installations, `npm` selects a PowerShell script that is blocked by the machine's execution policy.

Keep this window open and visit `http://localhost:3000` in your browser. Open `http://localhost:3000/register` to create an account.

## 5. Run the tests and checks

Run backend commands from the **backend folder** in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -m phase1 -q
.\.venv\Scripts\python.exe -m pytest tests\phase_1 -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
```

Run frontend commands from the **frontend folder** in PowerShell:

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

Expected result: each command finishes with exit code `0`. Pytest prints a passed-test count; Vitest prints the number of passing tests. The tests use the configured local PostgreSQL database and roll back their test data. The initial test run may apply the existing Alembic migration if the database has not been initialized yet.

## 6. Check authentication in the browser

1. In the site, choose **Create an account**. Enter a name, email, and password with 8–128 characters, at least one letter, and at least one number. The registration form should take you to `/login`.
2. Sign in with that email and password. The dashboard placeholder should open and the header should show your name and account menu.
3. Reload `/dashboard`. You should remain signed in.
4. Open browser developer tools with **F12**. In **Application** (Chrome/Edge) or **Storage** (Firefox), open the cookies for `localhost`. You should see `socratic_access` and `socratic_refresh`; both should have the **HttpOnly** flag. The **Secure** flag is enabled on HTTPS production deployments; local HTTP development does not set it.
5. In the developer tools console, run `document.cookie`. The two JWT cookies should not appear there because they are HttpOnly.
6. In the cookie table, delete only `socratic_access`, then reload `/dashboard`. The remaining refresh cookie should restore the access cookie and keep you signed in.
7. Delete both cookies and reload `/dashboard`. You should be redirected to `/login`.
8. Sign in again, open the header account menu, and choose **Sign out**. Both cookies should be removed and the browser should return to `/login`.

For a quick API check, visit `http://localhost:8000/docs`. The authentication endpoints are under `/api/v1/auth`; protected account endpoints are under `/api/v1/users`. The browser application itself never receives token values in its JSON responses.

## 7. Troubleshooting

- **`pg_isready` is not recognized:** PostgreSQL's `bin` folder is not on `PATH`. Start the PostgreSQL service from Windows Services, then use the full path to `pg_isready.exe` and `psql.exe` from that folder.
- **Database connection refused:** Check that the PostgreSQL service is running and that `DATABASE_URL` uses the right password, port, and database name. The backend terminal prints connection errors.
- **`JWT_SECRET must contain at least 32 bytes`:** Generate a new value with the command in section 3 and update the backend `.env` file.
- **The site says the authentication service is unavailable:** Confirm the backend is still running at `http://localhost:8000`, then reload the page.
- **PowerShell says scripts are disabled when running npm:** Use `npm.cmd` exactly as shown. No execution-policy change is needed.
- **`py -3.12` is not recognized:** Install Python 3.12 and select **Add Python to PATH** during setup. You can check installed versions with `py -0p`.
- **Port 3000 or 8000 is already in use:** Close the other development server using that port, then run the start command again.
- **Cookies are not marked Secure on localhost:** This is expected when using local HTTP. The production setting enables Secure cookies when the site runs over HTTPS.
- **`document.cookie` is empty:** This is expected for the JWT cookies. Confirm them in the browser's cookie storage panel, where their HttpOnly flags are shown.
