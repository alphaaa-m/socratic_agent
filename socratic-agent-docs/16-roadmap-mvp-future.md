# Roadmap, MVP and Future Enhancements

*Socratic Agent project document. [Index](README.md) | [← Previous](15-deployment.md) | [Next →](17-developer-guide.md)*

---

## 29. Development Roadmap

Durations are indicative for a team of one or two developers. Adjust them to the real team size.

| Phase | Name | Main tasks | Deliverables | Exit criteria | Duration |
|---|---|---|---|---|---|
| 1 | Project setup and authentication | Create the repository, `backend/` and `frontend/` skeletons, linting, CI, `.env.example`, local PostgreSQL database. Implement register, login, refresh, `/users/me`, JWT dependencies. Build login and registration pages and the BFF. | Running skeleton. Working auth end to end. | A user can register, log in and see a protected page. CI is green. | 1-2 weeks |
| 2 | PostgreSQL database and SQLAlchemy models | Implement all models (Section 7.2). Create the Alembic initial migration. Seed script. Constraint and cascade tests. | Migrated schema. Seed data. DB tests. | `alembic upgrade head` works. Schema matches Section 7.1. DB tests pass. | 1 week |
| 3 | FastAPI APIs | Subjects, sessions, messages (store only), assessments (read), progress (read), users, health. Error handling, rate limit, request ID. API tests. | OpenAPI documentation. API test suite. | All non-AI endpoints work. Authorization tests pass. | 2 weeks |
| 4 | Next.js frontend | Dashboard, subjects, chat UI, session history, progress page, admin pages (subjects, users). React Query hooks. Frontend tests. | Complete UI with a fake or stub reply. | A student can run a session with a stub agent end to end. | 2 weeks |
| 5 | Basic Socratic Agent | `LLMGateway`, LangChain models, prompt builder, dialogue engine, leak guard, hint ladder (manual hint button), conversation memory. `handle_student_message`. | Agent that asks guiding questions with a real LLM. | The agent asks guiding questions. The leak guard works on test prompts. | 2 weeks |
| 6 | Response evaluation and adaptive learning | Evaluator, misconception detector, adaptive controller, level estimator, resolution, session summary, fallback summary. Save assessments and agent state. | Evaluation, adaptation and summary in the full turn flow. | The Section 23 example passes as an integration test. | 2 weeks |
| 7 | RAG integration | Vector store interface, FAISS store, loaders, chunking, ingestion task, retriever, admin document pages, retrieval tester, `RAG_ENABLED` flag. | Documents improve answers. | Retrieval gold set meets the targets. Tutoring works with RAG off and on. | 2 weeks |
| 8 | Progress tracking | Mastery update, strengths and weaknesses, progress dashboard, trend chart, history filters. | Complete progress features. | Mastery and counters match Section 15.6 in tests. | 1 week |
| 9 | Testing | Fill test gaps. AI evaluation set and report. E2E tests. Security review. Performance check. Accessibility check. | Test reports. Evaluation report. | Quality gates in Section 24.10 pass. | 2 weeks |
| 10 | Deployment | Backend service setup (`uv run uvicorn`, no Docker), Vercel and Railway/Render setup, migrations on deploy, monitoring, backups, smoke test, user guide. | Production system. | The smoke test passes in production. The monitoring is active. | 1 week |

Total: about 16 weeks. Phases 3 and 4 can overlap. Phase 7 can move after the MVP release (Section 30).

---

## 30. MVP Definition

### 30.1 Scope

The MVP is the smallest release that shows the core value: a student learns through guided questions.

| # | MVP feature | Included detail |
|---|---|---|
| 1 | Authentication | Register, login, refresh, JWT, roles `student` and `admin`. |
| 2 | Subject selection | List of subjects. Administrator creates subjects (seeded). |
| 3 | Chat-based Socratic tutoring | Single Socratic Agent. Guiding questions, hint button, answer-leak guard, goal resolution. |
| 4 | Basic learner assessment | Evaluation of each answer (scores, misconception, feedback). Adaptive difficulty and hint level. Level estimate. |
| 5 | Conversation history | All messages saved. Session list and read-only view. |
| 6 | PostgreSQL persistence | All tables in Section 5. Alembic migrations. |
| 7 | Basic progress tracking | Mastery per subject, topics counts, level, strengths and weaknesses, session summary. |
| 8 | LLM integration | LangChain with Groq or Gemini (OpenAI/Anthropic also supported). |

### 30.2 Not in the MVP

- RAG with uploaded documents (`RAG_ENABLED=false`). The interfaces, tables and admin API stay in the code base. They are enabled in Release 1.1.
- Teacher dashboard, voice, mobile app, streaming replies, advanced analytics, social login.

### 30.3 MVP Acceptance Checklist

- [ ] A new user can register, log in and log out.
- [ ] A student can select a subject and start a session.
- [ ] In a 10-turn test conversation, the agent never states the final answer.
- [ ] Each student answer after the first has an assessment row.
- [ ] Difficulty and hint level change as the rules in Section 15 define.
- [ ] A student can ask for a hint with the button and in text.
- [ ] A student can end a session and read a summary (also when the LLM fails).
- [ ] The history page shows past sessions and messages.
- [ ] The progress page shows level, mastery and counts.
- [ ] All data is in PostgreSQL. A restart does not lose data.
- [ ] Authorization tests pass (a student cannot read another student's data).
- [ ] The system runs in production on Vercel and Railway or Render.

### 30.4 Release Plan

| Release | Content |
|---|---|
| **MVP (1.0)** | Features in 30.1. Phases 1-6, 8, 9 (core tests) and 10. |
| **1.1** | RAG (Phase 7 enabled), document management, retrieval metrics. |
| **1.2** | Quality improvements from the evaluation results. Streaming replies. |

---

## 31. Future Enhancements

| Enhancement | Description | Impact on design |
|---|---|---|
| Multiple subjects at scale | Subject hierarchy and topic tree. Prerequisites between topics. | Add `topics` table. Link sessions and progress to topics. |
| Advanced learner modeling | Per-topic mastery with a probabilistic model (for example, Bayesian knowledge tracing). Forgetting curve. | New `topic_mastery` table. Replace the EMA logic in `LevelEstimator`. |
| Better misconception detection | A catalog of known misconceptions for each subject. Match with embeddings. Remediation question bank. | New `misconceptions` table. Retrieval from a misconception index. |
| Voice interaction | Speech-to-text input and text-to-speech output. | New frontend components. New API for audio. Same agent. |
| Teacher dashboard | A `teacher` role. Classes and cohorts. Class progress. Common misconceptions. Consent-based access to conversations. | New tables (`classes`, `enrollments`). New permissions. |
| Advanced analytics | Learning curves, time on task, hint use, cohort comparison. Export. | Read replicas or an analytics schema. |
| More sophisticated RAG | Hybrid search (keyword and vector), re-ranking, query rewriting with the LLM, citations in answers, image and table extraction, `pgvector`. | Changes inside `app/rag/`. The agent interface stays the same. |
| Personalized learning plans | A recommended next-topic list and practice schedule from weaknesses and mastery. | New `learning_plans` table. New service. |
| Mobile application | React Native or a PWA that uses the same API. | The API stays the same. Add push notifications. |
| Streaming replies | Server-sent events for the tutor message. | New endpoint. Change the gateway to stream. Evaluation stays non-streaming. |
| Refresh-token revocation | Store refresh token IDs. Support logout everywhere. | New `refresh_tokens` table or a cache. |
| Message feedback | Thumbs up and down on agent messages. | New column or table. Feeds the evaluation set. |
| Multi-language | Tutor and UI in more languages. | Add `language` to preferences. Prompt templates per language. Check embedding model support. |

---

*[Index](README.md) | [← Previous](15-deployment.md) | [Next →](17-developer-guide.md)*
