# Phase 2: Subjects and Sessions (Student)

*[Index](README.md) | [← Phase 1](phase-1-authentication.md) | [Next: Phase 3 →](phase-3-chat-with-stub-agent.md)*

**Owner:** Student. **Time:** about 1 week. **Branch:** `phase-2/<your-name>`.

## 2.1 Goal

A student sees the active subjects, starts a tutoring session for one subject, and sees the list of own sessions. An administrator manages subjects and users. The dashboard, subject selection and history pages work.

## 2.2 Read First

| Topic | Design section |
|---|---|
| Requirements | §9.4 Subject selection, §9.5 Starting a session, §9.15 Learning history, §9.17 Account (admin part) |
| API | §18.5 Subject APIs, §18.6 Session APIs, §18.4 (admin user endpoints) |
| Data | §5.4.3 `subjects`, §5.4.4 `learning_sessions`, §6.3 cascade rules, §8.1 "Start session" |
| Sequence | §22.2 Starting a learning session |
| UI | §21.3 (dashboard, subject selection, history) |

## 2.3 Your Work List

```bash
grep -rn "TODO(phase-2)" backend frontend
```

### Backend

| # | Task | File | Notes |
|---|---|---|---|
| 1 | List and get subjects | `app/services/subject_service.py` | `list(active_only)` sorted by name. `get` gives `404` if missing. |
| 2 | Create, update, delete subjects (admin) | same | Duplicate name gives `409`. `update` can set `is_active=false` (retire). `delete`: `409` if the subject has sessions or documents (the database `RESTRICT` rule protects you, but check first and return a clear error). |
| 3 | Subject router | `app/api/v1/subjects.py` | List and get: any logged-in user. Create, update, delete: `AdminUser`. |
| 4 | Create session | `app/services/session_service.py` | Check the subject exists and is active (`404` otherwise). In **one transaction**: insert `learning_sessions` with `agent_state` from `AgentState(difficulty=<start from level>).model_dump()`, add 1 to `learner_profiles.total_sessions`, and upsert `learning_progress` (create the row if missing) with `topics_attempted` + 1. |
| 5 | List sessions | same | Own sessions only. Filters `subject_id`, `status`. Order by `started_at DESC`. Pagination with `limit` (max 100) and `offset`. Return `Page[SessionResponse]`. |
| 6 | Get session | same | Own session only. `404` for another user's session. Return `SessionDetailResponse` (messages are **not** included). |
| 7 | Session router | `app/api/v1/sessions.py` | `POST /sessions`, `GET /sessions`, `GET /sessions/{id}`. Leave `/end` and `/summary` as stubs (phase 6). |
| 8 | Admin users | `app/services/user_service.py`, `users.py` | `list_users` (filters `role`, `q` for name or email, pagination). `admin_update` (`role`, `is_active`). An admin cannot disable or demote **themself** (`400`). |

**Start difficulty:** use the map in §15.3 (beginner 2, intermediate 3, advanced 4). Put it in one place (a constant in `app/agents/capabilities/level_estimator.py` is the planned home, but that class is a stub until phase 5). For now, define `START_DIFFICULTY` in `app/services/session_service.py` and move it in phase 5.

### Frontend

| # | Task | File | Notes |
|---|---|---|---|
| 9 | API services and hooks | `services/subjects.ts`, `services/sessions.ts`, `hooks/useSubjects.ts`, `hooks/useSessions.ts` | Use `api<T>()` from `services/http.ts` and React Query. |
| 10 | Subject selection page | `app/(app)/subjects/page.tsx`, `components/subjects/SubjectCard.tsx`, `SubjectGrid.tsx` | One card for each subject. "Start session" calls `POST /sessions`, then goes to `/sessions/[id]`. Show a loading skeleton and an error toast. |
| 11 | Dashboard | `app/(app)/dashboard/page.tsx` | Greeting, "Start new session" button, last 5 sessions. (Level and mastery cards come in phase 6. Leave a placeholder card.) |
| 12 | History list | `app/(app)/sessions/page.tsx`, `components/history/SessionTable.tsx`, `SessionFilters.tsx` | Table with title, subject, status badge, date. Filters for subject and status. Pagination. Row click opens `/sessions/[id]`. |
| 13 | Admin subjects page | `app/(app)/admin/subjects/page.tsx` | Table, create and edit dialog, retire switch. Only for the admin role (check `GET /users/me`; the backend enforces it). |
| 14 | Admin users page | `app/(app)/admin/users/page.tsx` | Table, role select, active switch. |
| 15 | Sidebar | `components/layout/Sidebar.tsx` | Show the "Admin" group only for administrators. |

## 2.4 Hints

- For the upsert, use PostgreSQL `INSERT ... ON CONFLICT DO NOTHING` through SQLAlchemy: `from sqlalchemy.dialects.postgresql import insert`. Then `UPDATE ... SET topics_attempted = topics_attempted + 1` (an atomic increment in SQL, not read-modify-write in Python).
- Return `404`, not `403`, when a student asks for another student's session (§18.1).
- Put the ownership filter in the service query (`WHERE user_id = :me`), not in the router.
- `Page[T]` is generic. Use `Page[SessionResponse](items=..., total=..., limit=..., offset=...)`.
- For `total`, run a separate `SELECT count(*)` with the same filters.

## 2.5 Tests

| Test | Checks |
|---|---|
| List subjects | Only active by default. `active_only=false` shows retired ones. |
| Subject admin | Student gets `403` on create, update and delete. Admin succeeds. Duplicate name gives `409`. |
| Delete subject | `409` when a session exists. `204` when empty. |
| Create session | `201`. `status=active`, `ended_at=null`, `agent_state` has `difficulty`. `total_sessions` and `topics_attempted` increased by 1. A `learning_progress` row exists. |
| Create session twice | `topics_attempted` is 2 (the upsert does not create a second row). |
| Retired subject | Starting a session gives `404`. |
| List sessions | Only own sessions. Newest first. Filters and pagination work. |
| Get session | Owner gets `200`. Another student gets `404`. |
| Admin users | `403` for students. Filters work. An admin cannot demote themself. |
| Atomicity | If the progress upsert fails (mock an error), no session row is saved. |
| Frontend | `SubjectCard` start button calls the API. Filters update the query. |

## 2.6 Definition of Done

- [ ] All `TODO(phase-2)` markers are removed.
- [ ] Phase 2 tests and the full suite pass. Lint and type checks pass.
- [ ] A student can open `/subjects`, start a session, and arrive on the chat page (still a placeholder).
- [ ] The history page lists the new session. The dashboard shows it.
- [ ] An administrator can create, edit and retire a subject, and change a user's role. A retired subject disappears from the student list.
- [ ] In `psql`, a new session shows the right `agent_state` JSON.

## 2.7 Demo for the Instructor

1. Log in as a student. Start a session in "Python Programming".
2. Show the three database changes (`learning_sessions`, `learner_profiles.total_sessions`, `learning_progress.topics_attempted`).
3. Log in as admin. Retire a subject. Show that it is gone for the student.
4. Try to read the session of another user by ID. Show the `404`.

## 2.8 Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| Increasing counters in Python (`x = x + 1`) | Two requests at the same time lose an update. Use an SQL increment. |
| Creating the session and the counters in separate transactions | A failure leaves wrong data. Use one transaction. |
| Checking ownership only in the frontend | The API must enforce it. |
| Letting a student call admin endpoints because the UI hides the button | Always use `AdminUser` in the router. |
| Hard-deleting a subject that has history | The `RESTRICT` rule blocks it. Retire the subject instead. |
