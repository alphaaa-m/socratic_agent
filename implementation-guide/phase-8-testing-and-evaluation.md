# Phase 8: Testing, AI Evaluation and Hardening (Student)

*[Index](README.md) | [← Phase 7](phase-7-rag-faiss.md) | [Next: Phase 9 →](phase-9-deployment.md)*

**Owner:** Student. **Time:** 1 to 2 weeks. **Branch:** `phase-8/<your-name>`.

## 8.1 Goal

Prove that the system works and is safe. Close the gaps in the tests, measure the quality of the Socratic Agent, add end-to-end tests, and check security and accessibility. At the end, the quality gates of §24.10 pass.

## 8.2 Read First

| Topic | Design section |
|---|---|
| Test strategy | §24 (all) |
| AI metrics | §25 (all) |
| Security | §26 |
| Error handling | §27 |
| Non-functional requirements | §10 |

## 8.3 Your Work List

| # | Task | Where | Notes |
|---|---|---|---|
| 1 | Turn on the coverage gate | `.github/workflows/ci.yml` | `pytest --cov=app --cov-fail-under=80`. Add missing tests until the gate passes for `services` and `agents`. |
| 2 | Database tests | `tests/db/` | A test for each `CHECK`, `UNIQUE` and `NOT NULL` rule. Cascade tests (user, document, subject `RESTRICT`, uploader `SET NULL`). Migration test: `upgrade`, `downgrade`, `upgrade`, `alembic check`. Concurrency test for `TURN_CONFLICT`. |
| 3 | Error handling tests | `tests/api/` | One test for each row of §27.2 that applies: invalid input, auth failures, `409` cases, LLM failure (`503`), timeout (`504`), RAG error, empty retrieval, rate limit, invalid session. Check the standard error body and the `request_id`. |
| 4 | Authorization matrix test | `tests/api/test_authorization.py` | Parametrized test: for every endpoint in §18 call it with no token, student token and admin token. Compare with the permission matrix of §11.2. |
| 5 | Frontend tests | `frontend/**/*.test.tsx` | Components and hooks from §24.6. Add `jest-axe` checks on the login, subjects, chat and progress pages. |
| 6 | E2E tests | `frontend/e2e/` (Playwright) | The five flows of §24.9. Run against a test stack: Docker Compose database, backend with `LLM_PROVIDER=fake`, frontend. Provide a script `scripts/e2e.sh` to start it. |
| 7 | AI evaluation set | `backend/tests/ai/` | Build `scenarios.json` with **30 scenarios** across 3 subjects (core question, reference final answer, key concepts, simulated student profile: weak, average, strong). Reuse the scenarios from Phase 4. |
| 8 | Evaluation runner | `backend/tests/ai/run_eval.py` | Runs each scenario with simulated student answers (scripted lists of answers, or an LLM playing the student). Saves conversations as JSON. Computes the metrics below. Writes a Markdown report. |
| 9 | Rule-based metrics | `tests/ai/metrics.py` | Socratic behavior (has a question, 120 words or fewer, no leak phrases), leak rate (reference answer string match), hint safety, adaptation check (difficulty moves in the expected direction for strong and weak students). |
| 10 | Judge-based metrics | `tests/ai/judge.py` | A judge prompt (use a different model than the tutor if you can) scores guidance quality (1-5) and finds unsupported claims. Review 10% of the cases by hand. |
| 11 | Evaluation accuracy | `tests/ai/eval_accuracy.py` | Label 40 student answers by hand (correct, partial, wrong). Compare the evaluator scores. Report mean absolute error and agreement. |
| 12 | RAG quality | `tests/rag/` | Gold set from Phase 7: hit rate at k=4 and mean reciprocal rank. |
| 13 | Prompt-injection tests | `tests/ai/test_injection.py` | Student messages and document text with hidden instructions ("ignore previous rules", "print your system prompt"). The reply must not follow them. |
| 14 | Security review | `docs/security-checklist.md` | Go through §26 line by line. Mark each item with "done" and the proof (file or test). Run `pip-audit` and `npm audit`. Check that no secret is in Git history (`git log -p` search or `gitleaks`). |
| 15 | Performance check | `scripts/load_test.py` | 20 concurrent users for 2 minutes against the fake gateway: non-AI requests p95 ≤ 300 ms (NFR-PERF-01). Also check that database connections are not used during the (simulated slow) LLM call. |
| 16 | Accessibility check | manual | Keyboard-only run through the chat. Screen-reader labels. Contrast. Record the result. |
| 17 | Fix the findings | anywhere | Fix bugs found. Open an issue for any item that needs a design change (tell the instructor). |

## 8.4 Metrics and Targets

Use the table in §25.2. Fill in the results in a report `docs/evaluation-report.md`:

| Metric | Target | Result | Notes |
|---|---|---|---|
| Final-answer leak rate | ≤ 2% | | |
| Socratic behavior | ≥ 95% | | |
| Hint safety | ≥ 99% | | |
| Guidance quality (judge, mean) | ≥ 4.0 | | |
| Evaluation accuracy (MAE of c and r) | ≤ 0.15 | | |
| Adaptation quality | ≥ 95% rule compliance | | |
| RAG hit rate at k=4 | ≥ 0.85 | | |
| Hallucination rate with RAG | ≤ 5% | | |
| Resolution within 10 turns (simulated) | ≥ 70% | | |
| Latency p95 per turn (live) | ≤ 8 s | | |

If a metric misses the target: write down the cause, the change you tried, and the new result. A missed target with a clear analysis is acceptable. A target with no measurement is not.

## 8.5 Hints

- Use the **fake gateway** for logic tests and a **live model** only for the evaluation runner. Mark live tests with `@pytest.mark.live` and keep them out of the normal CI run.
- Save the conversation JSON of each run. You need it to find why a metric dropped.
- Keep the temperature at 0 for the judge and the evaluator.
- Simulated students: scripted answers are the most repeatable. An LLM student is more realistic but changes between runs. Use scripted answers for CI and LLM students for the report.
- One failing scenario is more useful than ten passing ones. Add every real bug as a new scenario.
- The leak check by string match can miss a rephrased answer. Add the judge check ("does this message state the final answer?").

## 8.6 Definition of Done

- [ ] Backend coverage for `services` and `agents` is 80% or more. The CI gate is on.
- [ ] The authorization matrix test passes for every endpoint.
- [ ] All E2E flows pass.
- [ ] `docs/evaluation-report.md` has a measured value for every metric, with notes for any miss.
- [ ] `docs/security-checklist.md` is complete. No high-severity finding is open.
- [ ] The prompt-injection tests pass.
- [ ] `alembic check`, `ruff`, `eslint`, `tsc` and all tests pass in CI.

## 8.7 Demo for the Instructor

1. Show the CI run with the coverage gate.
2. Run one E2E flow in the browser (Playwright headed mode).
3. Run the evaluation runner on 3 scenarios and show the report and one saved conversation.
4. Show 2 prompt-injection attempts and the replies.
5. Walk through the security checklist.

## 8.8 Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| Tests that only check the status code | A `201` with wrong data is still a bug. Check the body and the database. |
| Using the same model as tutor and judge | The judge tends to prefer its own style. Use a different model if possible. |
| Reporting only the metrics that look good | The report must show all metrics. |
| Live LLM calls in the normal CI run | Slow, costly and not repeatable. |
| E2E tests that depend on each other | Each flow must create its own data. |
| Ignoring `npm audit` and `pip-audit` results | Record each finding and your decision. |
