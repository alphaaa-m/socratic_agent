# Phase 5: Evaluation and Adaptive Learning (Student)

*[Index](README.md) | [← Phase 4](phase-4-socratic-agent-core.md) | [Next: Phase 6 →](phase-6-summary-and-progress.md)*

**Owner:** Student. **Time:** about 2 weeks. **Branch:** `phase-5/<your-name>`.

## 5.1 Goal

The agent evaluates each student answer, finds misconceptions, estimates the learner level, and adapts the difficulty and the hints. The assessment is saved. The agent detects when the student reaches the correct reasoning. The UI shows feedback and the session status.

## 5.2 Read First

| Topic | Design section |
|---|---|
| Rules and formulas | §15 (all). This is the most important section of the phase. |
| Evaluation prompt | §16.6 |
| Data contracts | §14.3 (`EvaluationResult`, `AgentState`, `LearnerUpdate`) |
| Pipeline | §14.4, §14.5 |
| Data flow | §8.1 (Evaluate response, Update learning state), §8.2 |
| Example to reproduce | §23 (the full session with all numbers) |
| Metrics | §25 (evaluation accuracy, adaptation quality) |

## 5.3 Your Work List

```bash
grep -rn "TODO(phase-5)" backend frontend
```

| # | Task | File | Notes |
|---|---|---|---|
| 1 | Evaluation in the gateway | `LangChainGateway.evaluate` | Use the **judge model** (temperature 0) with `with_structured_output(EvaluationResult)`. If the output is invalid, repeat **once**. After that, raise `LLMUnavailableError` (FR-EVA-06). |
| 2 | Evaluation prompt | `app/agents/prompts/` | From §16.6. Put student text in `<student_message>` tags. |
| 3 | Response evaluator | `capabilities/response_evaluator.py` | `evaluate(turn, state)`: build the messages (core question, last agent question, chunks if any, student answer) and call the gateway. |
| 4 | Misconception detector | `capabilities/misconception_detector.py` | `normalize(evaluation)`: lowercase, trim, remove end punctuation, limit to 120 characters. Empty label becomes `None`. |
| 5 | Adaptive controller | `capabilities/adaptive_controller.py` | `performance`, `apply`, `raise_hint`, `select_mode` from §15. Constants in one place. Update streaks, difficulty, hint level, `stuck_turns`, `misconceptions`, `demonstrated_concepts`, `perf_history`, `resolved`. |
| 6 | Level estimator | `capabilities/level_estimator.py` | `initial_difficulty`, `update` with the EMA and hysteresis (§15.3). Move `START_DIFFICULTY` here from `session_service.py` and import it there. |
| 7 | Calibration | `adaptive_controller.py` or `prompt_builder.py` | Compute `overconfident`, `underconfident`, `calibrated` (§15.5). Pass it to the student context block. |
| 8 | Recurring misconceptions | `prompt_builder.py` | Add labels with count ≥ 2 to the student context block (§16.3). |
| 9 | Pipeline | `socratic_agent.py` → `handle_turn` | Add the evaluation branch from §14.4: evaluate → normalize → apply → level update → `select_mode`. If `state.resolved`, use `dialogue.closing_reply` (mode `close`, §16.4) and skip retrieval. Add the `worked_analogy` mode text. |
| 10 | Save assessments | `TutoringService.handle_student_message` (write phase) | Insert `LearnerAssessment` for the student message with `difficulty_used`, `resolves_goal=new_state.resolved`. Update `learner_profiles` (`level_score`, `assessment_count`, `current_level`). Update `learning_progress.last_activity_at`. All in the **same** write transaction. |
| 11 | Assessment APIs | `app/services/assessment_service.py`, `app/api/v1/assessments.py` | `GET /sessions/{id}/assessments`, `GET /assessments/{id}`. Own data only (`404` otherwise). |
| 12 | Response fields | `_to_response` | Fill `assessment` and `session_state` (`difficulty`, `hint_level`, `resolved`, `learner_level`). |

### Frontend

| # | Task | File | Notes |
|---|---|---|---|
| 13 | Feedback chip | `components/chat/FeedbackChip.tsx` | Show `assessment.feedback` under the student's message. Do **not** show the misconception label or the raw scores. |
| 14 | Status bar | `SessionStatusBar.tsx` | Level badge, difficulty dots, hint level from `session_state`. Animate changes lightly. |
| 15 | Resolved banner | `components/chat/ResolvedBanner.tsx` | When `session_state.resolved` is true: show "You reached the answer" and disable the input. (The end-session action comes in Phase 6.) |

## 5.4 Hints

- **Implement the rules from §15 yourself first.** Section 15.8 has reference code. Use it only to check your work after your tests pass. Your tests should come from the rules, not from the code.
- Write the unit tests for the adaptive controller **before** the code. The table in §15.4 gives you the test cases.
- The two hardest cases: (1) a high turn that also asks for a hint, (2) `hint_level` after a high turn. Write a test for both.
- `perf_history` stores `p` for each assessment. The mastery calculation in Phase 6 needs it.
- Round the stored scores to 3 decimals (`NUMERIC(4,3)`).
- Keep the evaluator output **strict**: validate that scores are between 0 and 1. Pydantic does this with `Field(ge=0, le=1)`.
- The evaluation can be wrong. Use the `FakeGateway.eval_queue` to give **exact** results in tests. Never test the math with a live LLM.
- The `difficulty_level` of an assessment is the difficulty of the question the student **answered** (before the update).

## 5.5 Tests

| Test | Checks |
|---|---|
| Adaptive controller (unit) | `p` boundaries 0.75 and 0.40. Two high turns raise difficulty. Two low turns lower difficulty and raise the hint level. Difficulty stays in 1..5. Hint level stays in 0..3. High turn lowers the hint level. Hint request raises it. Neutral turn resets streaks. Stuck policy gives `worked_analogy`. |
| Resolution (unit) | Needs `addresses_core_question` and `c ≥ 0.85` and `r ≥ 0.75`. A correct partial answer does not resolve. |
| Level estimator (unit) | EMA values. No level change before 5 assessments. Promotion and demotion thresholds. Hysteresis (no flip-flop). |
| Misconception detector (unit) | Normalization. Empty becomes `None`. Length limit. |
| Calibration (unit) | Over, under and calibrated cases. |
| Evaluator (unit) | Builds messages with the right parts. Invalid output is repeated once, then fails. |
| **Example session (integration)** | Replay §23 with a scripted `FakeGateway` (`eval_queue` and `reply_queue`). Assert: `p` = 0.355, 0.855, 0.9275. `level_score` = 0.304, 0.397, 0.485. `hint_level` after turn 1 is 1 and after turn 2 is 0. `resolved` is true at turn 3. Three assessment rows. `learner_profiles.assessment_count` is 3. |
| Persistence | Assessment row has the right `message_id`, `difficulty_level` and `resolves_goal`. Profile updated in the same transaction. |
| Failure | Evaluator failure gives `503` and **no** rows (not even the student message). |
| API | `GET /sessions/{id}/assessments` returns own data. Another user gets `404`. |
| Frontend | Feedback chip shows feedback only. Resolved banner disables input. |

## 5.6 Definition of Done

- [ ] All `TODO(phase-5)` markers are removed.
- [ ] Phase 5 tests and the full suite pass. Lint and type checks pass.
- [ ] The §23 example test passes with the exact numbers.
- [ ] With a real LLM, a strong simulated student (you, giving good answers) makes the difficulty rise. A weak one (vague answers) makes it fall and the hints increase.
- [ ] A correct and complete answer resolves the session. The agent sends a closing message.
- [ ] Every student response after the first has one row in `learner_assessments`.
- [ ] The student sees feedback text, level and difficulty. The student does **not** see raw scores or misconception labels in the UI.

## 5.7 Demo for the Instructor

1. Run the §23 example test and explain each number in the table.
2. In the UI, answer badly twice. Show the difficulty drop and the hint level rise in the status bar and in `agent_state`.
3. Answer well twice. Show the difficulty rise.
4. Give the complete correct answer. Show the closing message and `resolves_goal = true`.
5. Show the `learner_profiles` row (`level_score`, `assessment_count`).

## 5.8 Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| Putting confidence into the performance score | It rewards overconfidence. The design uses confidence only for calibration. |
| Mutating the profile in the agent | The agent is pure. It returns a `LearnerUpdate`. The service saves it. |
| Updating the state before the evaluation succeeds | A failed evaluation must leave the state unchanged. Work on a **copy** (the agent already does `model_copy`). |
| Changing the level after 1 or 2 answers | The design needs 5 assessments and uses hysteresis. |
| Using `difficulty` after the update for the assessment row | Store the difficulty of the question that was answered. |
| Testing the formulas with a live LLM | Results change between runs. Use fixed `EvaluationResult` objects. |
| Showing numeric scores to students | Scores can discourage students. The MVP shows feedback text only (OD-04). |
