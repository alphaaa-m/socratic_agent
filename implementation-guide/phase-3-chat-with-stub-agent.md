# Phase 3: Chat with a Stub Agent (Student)

*[Index](README.md) | [← Phase 2](phase-2-subjects-and-sessions.md) | [Next: Phase 4 →](phase-4-socratic-agent-core.md)*

**Owner:** Student. **Time:** 1 to 1.5 weeks. **Branch:** `phase-3/<your-name>`.

## 3.1 Goal

A student can chat in a session. Every message is saved. The agent answers with a **canned reply** from the `FakeGateway`. The real transaction flow, the hint button and the chat UI all work. In Phase 4 you replace the fake reply with a real LLM and you will not need to change the service or the UI.

## 3.2 Read First

| Topic | Design section |
|---|---|
| Requirements | §9.6 Sending questions, §9.12 Conversation history, §9.10 Hint (button part) |
| API | §18.7 Message APIs, §18.13 (send message example) |
| Transactions | §8.2 Transaction and concurrency rules, §19.5 Tutoring service |
| Agent contract | §14.3 data contracts, §14.4 turn pipeline |
| Sequence | §22.3 First turn |
| UI | §21.2 Chat screen |

## 3.3 Your Work List

```bash
grep -rn "TODO(phase-3)" backend frontend
```

### Backend

| # | Task | File | Notes |
|---|---|---|---|
| 1 | List messages | `app/services/tutoring_service.py` → `list_messages` | Own session only (`404` otherwise). Order by `created_at, id`. Pagination. |
| 2 | Read phase | `_load_context` (private method) | In a short transaction, read: session (check owner and `status == "active"`, else `409 SESSION_NOT_ACTIVE`), learner profile, subject, last 10 messages, message count. Build `AgentState` from `session.agent_state`. Build `ProfileSnapshot`. Then **end the transaction** (`db.rollback()` or `db.commit()`), so no connection is held during the agent call. |
| 3 | Agent call | `handle_student_message` | Build `AgentTurnInput` (`kind="question"` if the session has no messages, else `"response"`). Call `self.agent.handle_turn(turn)`. |
| 4 | Write phase | same | In **one** transaction: lock the session row (`SELECT ... FOR UPDATE`), compare `agent_state["turn_index"]` with the value from the read phase (`TurnConflictError` if different), insert the student message and the agent message, update `agent_state`, and set `title` from the first question (60 characters). If anything fails, nothing is saved. |
| 5 | Stub agent turn | `app/agents/socratic_agent.py` → `handle_turn` | **Minimal version only:** call `gateway.generate_reply(...)` with a simple message list and return an `AgentTurnOutput` with `evaluation=None`, the same `learner_update`, no chunks, `rag_status="off"`, and `turn_index + 1`. Mark with `# TODO(phase-4): replace with the full pipeline`. |
| 6 | Hint request | `handle_hint_request` | Same three parts, with `kind="hint_request"`. Save only the agent message (`message_type="hint"`). Raise the hint level by 1 (maximum 3) and add 1 to `hints_used` in the new state. No student message. |
| 7 | Response mapping | `_to_response` | Build `SendMessageResponse` and `SessionStateResponse` from the saved data. |
| 8 | Routers | `app/api/v1/messages.py` | Wire the three endpoints (§18.14 shows the pattern). Add the rate limit `20/minute` on the two POST endpoints. |

**Important rule for the stub agent:** the agent must not import SQLAlchemy. If you need data, the service gives it to the agent in `AgentTurnInput`.

### Frontend

| # | Task | File | Notes |
|---|---|---|---|
| 9 | API services and hooks | `services/messages.ts`, `hooks/useMessages.ts`, `hooks/useSendMessage.ts`, `hooks/useHint.ts` | `useSendMessage` is a mutation with an **optimistic update**: add the student message to the cache at once. Replace it with the saved messages when the response arrives. On error, remove it, restore the input text and show a toast. |
| 10 | Chat window | `components/chat/ChatWindow.tsx`, `MessageBubble.tsx` | Agent messages on the left, student messages on the right. Hint messages have a lightbulb style. `ScrollArea` scrolls to the newest message. `role="log"` and `aria-live="polite"`. |
| 11 | Message input | `components/chat/MessageInput.tsx` | `Textarea`. `Enter` sends. `Shift+Enter` adds a line. Counter for 4000 characters. Disabled while sending. |
| 12 | Hint button | `components/chat/HintButton.tsx` | Calls `POST /sessions/{id}/hints`. Disabled while a request runs. |
| 13 | Typing indicator | `components/chat/` | `Skeleton` bubble while the agent responds. |
| 14 | Status bar | `components/chat/SessionStatusBar.tsx` | Show level, difficulty (dots) and hint level from `session_state`. |
| 15 | Session page | `app/(app)/sessions/[sessionId]/page.tsx` | Load the session and the messages. If the session is not `active`, show the messages **read-only** (no input). Handle `409 TURN_CONFLICT` by reloading the messages. |
| 16 | End-session button | `components/chat/` | Show the button but keep it **disabled** with the tooltip "Available in phase 6". |

## 3.4 Hints

- The message count decides the first turn: `message_count == 0`.
- The write phase is the heart of the project. Draw the three parts on paper first: read → agent → write.
- For the row lock in SQLAlchemy: `select(LearningSession).where(LearningSession.id == sid).with_for_update()`.
- `agent_state` is a JSONB column. SQLAlchemy does not detect an in-place change to a dict. Assign a **new** dict: `session.agent_state = out.new_state.model_dump()`.
- Do not hold the transaction open while the agent runs. Test it: make the `FakeGateway` sleep and check in `pg_stat_activity` that the connection is idle.
- A student `question` is the first message. All later student messages are `response`. The database `CHECK` rule `sender_type_consistent` will reject a wrong combination.
- The FakeGateway lets you queue replies: `fake_gateway.reply_queue.append(TutorReply(...))`.

## 3.5 Tests

| Test | Checks |
|---|---|
| First message | `201`. Student message type `question`. Agent message `guidance`. `assessment` is `null`. Title set from the question. `turn_index` is 1. |
| Second message | Student message type `response`. |
| Ordering | `GET messages` returns time order. Pagination works. |
| Ownership | Another user gets `404` on list and send. |
| Inactive session | `409 SESSION_NOT_ACTIVE` (set the status in the test database). |
| Validation | Empty text and text over 4000 characters give `422`. |
| Atomicity | `fake_gateway.fail_next("generate_reply")` → `503`, and **no** message rows exist. |
| Turn conflict | Change `agent_state.turn_index` between the read phase and the write phase (patch `_load_context`). Result: `409 TURN_CONFLICT` and nothing saved. |
| Hint | `201`. Message type `hint`. `hint_level` is 1. `hints_used` is 1. No student message added. A fourth hint keeps the level at 3. |
| Rate limit | The 21st request in a minute gives `429`. |
| No connection during agent call | The agent is called when no transaction is open (assert with a spy). |
| Frontend | Optimistic update appears at once and is replaced. Error restores the text. Enter and Shift+Enter work. |

## 3.6 Definition of Done

- [ ] All `TODO(phase-3)` markers are removed (except those in `socratic_agent.py` marked `phase-4`).
- [ ] Phase 3 tests and the full suite pass. Lint and type checks pass.
- [ ] In the browser, a student starts a session, sends 3 messages, presses the hint button, reloads the page, and sees the full conversation.
- [ ] In `psql`: `messages` rows have the right `sender` and `message_type`. `learning_sessions.agent_state.turn_index` increases by 1 for each turn.
- [ ] The failure test proves that no partial data is saved.

## 3.7 Demo for the Instructor

1. Chat in the UI. Show the optimistic update and the typing indicator.
2. Press the hint button. Show the new `hint` row and the `hint_level` change.
3. Stop the fake gateway with `fail_next` (use a test endpoint or a pytest run). Show `503` and the unchanged tables.
4. Explain the three parts of the flow and why the transaction is not open during the agent call.

## 3.8 Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| Saving the student message before the agent runs | If the LLM fails, the conversation has a student message without a reply. The design saves a turn completely or not at all. |
| Holding the database session open during the LLM call | Uses up connections when many students chat. |
| Mutating `agent_state` in place | The change is not saved (JSONB mutation is not tracked). |
| Reading the session again in the write phase and trusting the new `turn_index` | You must compare with the value from the **read** phase. |
| Putting the agent call inside the router | Routers must not contain business logic. |
| Letting the agent import `Session` or models | Breaks design rule R-02. |
