# Phase 6: Session Summary and Progress (Student)

*[Index](README.md) | [← Phase 5](phase-5-evaluation-and-adaptive.md) | [Next: Phase 7 →](phase-7-rag-faiss.md)*

**Owner:** Student. **Time:** about 1 week. **Branch:** `phase-6/<your-name>`.

## 6.1 Goal

A student ends a session and reads a structured summary. The system updates mastery, strengths and weaknesses. The student sees progress on a dashboard and can open past sessions. The student can delete the own account. **After this phase the MVP features are complete.**

## 6.2 Read First

| Topic | Design section |
|---|---|
| Requirements | §9.13 Progress, §9.14 Summaries, §9.15 History, §9.17 Account |
| Formulas | §15.5 (misconceptions to weaknesses), §15.6 (mastery) |
| Summary prompt | §16.6.1 |
| API | §18.6 (`/end`, `/summary`), §18.9 Progress APIs, §18.13 (end session example) |
| Data flow | §8.1 "End session" |
| Sequence | §22.6 Session completion |
| Errors | §27.2 (summary failure: fallback) |
| UI | §21.3 (progress dashboard, summary dialog) |

## 6.3 Your Work List

```bash
grep -rn "TODO(phase-6)" backend frontend
```

### Backend

| # | Task | File | Notes |
|---|---|---|---|
| 1 | Summary in the gateway | `LangChainGateway.summarize_session` | Structured output `SessionSummary`. Use the retry policy from Phase 4. |
| 2 | Summary prompt | `app/agents/prompts/` | From §16.6.1. Input: core question, conversation, assessments (scores and misconceptions), outcome. Rule: if the outcome is not `resolved`, do not state the final answer. |
| 3 | Session summarizer | `capabilities/session_summarizer.py` | `summarize(data, outcome)` calls the gateway. On **any** gateway error, return the **fallback summary** (`generated_by="fallback"`): built only from stored data (outcome, number of turns, demonstrated concepts, misconceptions, hint count, a fixed text for next steps). |
| 4 | Agent facade | `socratic_agent.py` → `summarize` | Delegates to the summarizer. |
| 5 | Mastery functions | `app/services/progress_service.py` (pure helper functions) | `session_score(perf_history, hints_used)` and `update_mastery(old, score, is_first)` exactly as §15.6. Keep them free of database code so tests are easy. |
| 6 | Strengths and weaknesses | same | `merge_weaknesses` and `merge_strengths` (§15.5): counts, `last_seen_at`, limit of 10, oldest and lowest count leave first. |
| 7 | Apply session result | `ProgressService.apply_session_result` | For `completed` sessions: update `mastery_score` (EMA or first-session rule), add 1 to `topics_mastered` if the score is ≥ 0.75, set `last_activity_at`. For `abandoned`: only `last_activity_at`. `is_first` means no earlier `completed` session for this user and subject. |
| 8 | End session | `SessionService.end_session` | **Read phase:** load session, messages, assessments, state (own and `active` only, else `404` / `409`). **Agent phase:** `agent.summarize(...)`. Outcome: `resolved` state gives `completed`, otherwise `abandoned`. **Write phase (one transaction):** lock the session, check again that it is `active`, set `status`, `ended_at` and `summary`, insert the `summary` message (sender `agent`), call `apply_session_result`, update `learner_profiles` (strengths and weaknesses). A second call gives `409`. |
| 9 | Summary endpoint | `GET /sessions/{id}/summary` | `404` if there is no summary. |
| 10 | Progress APIs | `ProgressService.overview`, `for_subject`, `app/api/v1/progress.py` | `overview`: level, level score, total sessions, strengths, weaknesses, one `ProgressResponse` for each subject. `for_subject`: progress plus a trend (the session score of the last 10 completed sessions, computed from `agent_state.perf_history` or stored summary data). Return `404` for an unknown subject. |
| 11 | Delete account | `UserService.delete_me` (check) | Make sure the cascade removes sessions, messages, assessments, progress and profile. Add a test that counts rows in every table. |

> **Trend data:** the schema has no column for the session score. Compute it again from the stored `perf_history` in `agent_state`. Do **not** ask for a schema change.

### Frontend

| # | Task | File | Notes |
|---|---|---|---|
| 12 | End session | `components/chat/EndSessionButton.tsx`, `SummaryDialog.tsx` | `AlertDialog` for confirmation. Call `POST /sessions/{id}/end`. Show the summary in a `Dialog` with sections: overview, key concepts, strengths, corrected misconceptions, areas to review, next steps. When `resolved` is true, end the session automatically after one click on the banner. |
| 13 | Read-only history view | `app/(app)/sessions/[sessionId]/page.tsx` | For ended sessions: messages read-only and a "View summary" button. |
| 14 | Progress page | `app/(app)/progress/page.tsx`, `components/progress/*` | `LevelBadge`, `MasteryCard` for each subject (mastery bar, topics attempted and mastered), `TrendChart` (Recharts line chart), `WeaknessList` and strengths as `Badge` lists. `Tabs` for subjects. |
| 15 | Dashboard cards | `app/(app)/dashboard/page.tsx` | Replace the placeholder with level and mastery cards. |
| 16 | Delete account | `app/(app)/settings/page.tsx` (new) | Name change, password change, delete account (`AlertDialog`; type "DELETE" to confirm). After deletion, clear cookies and go to `/login`. |

## 6.4 Hints

- Never call the LLM inside the write transaction (§8.2). Order: read → summarize → write.
- If the LLM fails, **still end the session**. The student should not be stuck in a session that cannot end.
- Compute the mastery with the **last 3** values of `perf_history`. A session with fewer than 3 assessments uses what it has. A session with 0 assessments has score 0 (and is normally `abandoned`).
- `topics_mastered` must never exceed `topics_attempted`. The database `CHECK` rule will reject a wrong update. Use it as a test.
- Use `db.scalar(select(func.count())...)` to find `is_first`.
- Use the numbers in the §23 example as a test: session score 0.6625, first completed session, mastery 0.663, `topics_mastered` stays 0.

## 6.5 Tests

| Test | Checks |
|---|---|
| `session_score` (unit) | Last 3 average. Hint penalty (0.05 each, maximum 4). Never below 0. Fewer than 3 values. |
| `update_mastery` (unit) | First session sets the score. Later sessions use 0.70 / 0.30. |
| Strengths and weaknesses (unit) | Count increments, limit of 10, removal order. |
| Fallback summary (unit) | Contains outcome and counts. `generated_by="fallback"`. No LLM call. |
| End session (integration) | Status `completed` when resolved, `abandoned` otherwise. `ended_at` set. `summary` saved. A `summary` message added. Mastery and counters updated. |
| §23 example | Mastery 0.663. `topics_attempted` 1. `topics_mastered` 0. |
| Abandoned | Mastery unchanged. `last_activity_at` updated. |
| LLM failure | `fail_next("summarize_session")`: status `200`, fallback summary, session ended. |
| Second end call | `409`. |
| Atomicity | An error in the progress update rolls back the whole end-session write. |
| Ownership | Another student gets `404` on `/end` and `/summary`. |
| Progress API | Overview contains all subjects with progress. Trend has at most 10 values. Unknown subject gives `404`. |
| Delete account | Row counts for the user are 0 in all tables. |
| Frontend | Summary dialog shows all sections. Delete needs the typed confirmation. |

## 6.6 Definition of Done

- [ ] All `TODO(phase-6)` markers are removed.
- [ ] Phase 6 tests and the full suite pass. Lint and type checks pass.
- [ ] **MVP check:** run the full list in §30.3. Every item is checked.
- [ ] A student completes a full session in the browser (question → hints → resolved → end → summary) and sees updated progress.
- [ ] Ending a session while the LLM key is wrong still works and shows a fallback summary.
- [ ] After account deletion, `psql` shows no rows for that user anywhere.

## 6.7 Demo for the Instructor

1. Run a complete session in the UI. End it. Show the summary.
2. Show the database changes: `learning_sessions` (status, summary), `messages` (summary row), `learning_progress`, `learner_profiles`.
3. Break the LLM key and end another session. Show the fallback summary.
4. Show the progress page and the trend chart.
5. Delete the account and show the empty tables.

## 6.8 Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| Updating mastery for abandoned sessions | The design changes mastery only for completed sessions. |
| Calling the LLM inside the write transaction | Holds a connection and a lock for many seconds. |
| Failing the whole request when the summary fails | The design requires a fallback (FR-SUM-03). |
| Counting `topics_mastered` twice | The session can end only once (check `status` under the row lock). |
| Reading the trend from a table that does not exist | Compute it from `perf_history`. Do not change the schema. |
| Showing the final answer in the summary of an abandoned session | The summary prompt forbids it. Test it. |
