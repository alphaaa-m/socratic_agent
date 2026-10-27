# Phase 3: Chat with a Stub Agent — Windows Test Guide

Phase 3 adds the saved student/tutor conversation and uses `LLM_PROVIDER=fake`.
These commands use the existing local database safely: migrations only upgrade it;
pytest uses transactional rollback and does not drop or reset data.

## Automated verification

Start PostgreSQL, then run these commands from PowerShell. Use `npm.cmd` rather
than `npm` when PowerShell blocks the `npm.ps1` shim.

```powershell
cd C:\Users\User\Desktop\Socratic_Agent\socratic_agent\backend
uv run alembic upgrade head
uv run pytest tests/phase_3 -q
uv run pytest -q
uv run ruff check app tests
uv run python -m compileall app
```

The Phase 3 test group checks first and later student turns, ordered/paged
history, ownership, inactive-session rejection, request validation, no partial
messages after a gateway failure, turn conflict handling, hints, the per-user
rate limit, and that the database transaction is closed during the gateway call.

```powershell
cd C:\Users\User\Desktop\Socratic_Agent\socratic_agent\frontend
npm.cmd test
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

The frontend tests cover accessible message rendering, hint rendering, keyboard
send behavior, the 4,000-character limit, optimistic replacement, and error
rollback. `npm.cmd run lint` may report that `next lint` is unavailable in newer
Next.js releases; record that output and use the TypeScript check until the
project’s lint script is updated.

## Manual browser flow

1. Ensure `backend\.env` has `LLM_PROVIDER=fake`; do not add provider keys.
2. Start the API from `backend` with `uv run uvicorn app.main:app --reload`.
3. Start the frontend from `frontend` with `npm.cmd run dev`.
4. Register and sign in, open **Subjects**, and start a session.
5. Send a question. It appears immediately at the right, followed by the fake
   tutor guidance at the left. Reload and confirm both saved messages remain.
6. Send two more messages, press **Get a hint**, and confirm the yellow hint
   bubble and the hint level change. A fourth hint remains at level `3/3`.
7. Press Enter to send; use Shift+Enter to make a new line. Confirm the counter
   reaches `4000/4000` and sending is disabled while a reply is pending.
8. In a completed or abandoned session, confirm the conversation remains visible
   while the composer is absent. Hover the disabled **End session** button in an
   active session to see “Available in phase 6”.

## Optional read-only database checks

Replace `YOUR_EMAIL` with the account used above. These queries only read data.

```powershell
psql -U postgres -d socratic_agent -c "SELECT s.id, s.title, s.status, s.agent_state FROM learning_sessions s JOIN users u ON u.id = s.user_id WHERE u.email = 'YOUR_EMAIL' ORDER BY s.started_at DESC;"
psql -U postgres -d socratic_agent -c "SELECT m.sender, m.message_type, m.content, m.created_at FROM messages m JOIN learning_sessions s ON s.id = m.session_id JOIN users u ON u.id = s.user_id WHERE u.email = 'YOUR_EMAIL' ORDER BY m.created_at, m.id;"
```

The first student row is `question`; later student rows are `response`; tutor
rows are `guidance` or `hint`. `agent_state.turn_index` rises once per submitted
message or hint, and hint requests add only an agent `hint` row.
