# Final Consistency Check

*Socratic Agent project document. [Index](README.md) | [← Previous](17-developer-guide.md)*

---

## 33. Final Output Requirements and Consistency Check

### 33.1 Summary

This document describes one integrated system: **Next.js + FastAPI + PostgreSQL + LangChain + RAG + LLM**, with **one Socratic Agent** that has ten internal capabilities. The same names and rules are used in the requirements, database, API, backend, frontend and AI sections.

### 33.2 Traceability Matrix

| Feature | Requirements | Use case | Tables | Endpoints | Backend modules | Frontend |
|---|---|---|---|---|---|---|
| Registration, login, JWT | FR-REG, FR-LOG, FR-JWT | UC-01, UC-02 | `users`, `learner_profiles` | `/auth/*`, `/users/me` | `auth/`, `auth_service` | `(auth)/login`, `(auth)/register`, BFF |
| Subjects | FR-SUB | UC-03 | `subjects` | `/subjects*` | `subject_service` | `/subjects`, `/admin/subjects` |
| Session | FR-SES, FR-HIS | UC-03, UC-09 | `learning_sessions` | `/sessions*` | `session_service` | `/sessions`, `/sessions/[id]` |
| Socratic dialogue | FR-MSG, FR-SOC | UC-04, UC-05, UC-08 | `messages` | `/sessions/{id}/messages` | `tutoring_service`, `agents/` | `components/chat` |
| Evaluation | FR-EVA | UC-06, UC-07 | `learner_assessments` | `/sessions/{id}/assessments`, `/assessments/{id}` | `response_evaluator`, `misconception_detector` | `FeedbackChip` |
| Adaptive learning and hints | FR-ADP, FR-HNT | UC-05, UC-08 | `learning_sessions.agent_state`, `learner_profiles` | `/sessions/{id}/hints` | `adaptive_controller`, `level_estimator`, `hint_generator` | `SessionStatusBar`, `HintButton` |
| RAG | FR-RAG | UC-04, UC-08 | `messages.retrieved_chunk_ids` | (internal) | `rag/`, `knowledge_retriever` | - |
| Summary | FR-SUM | UC-09 | `learning_sessions.summary`, `messages` | `/sessions/{id}/end`, `/summary` | `session_summarizer` | `SummaryDialog` |
| Progress | FR-PRG | UC-10 | `learning_progress`, `learner_profiles` | `/progress*` | `progress_service` | `/progress`, `/dashboard` |
| Documents | FR-DOC | UC-11 | `knowledge_documents`, `document_chunks` | `/documents*` | `document_service`, `rag/ingestion` | `/admin/documents` |
| Account and privacy | FR-ACC | - | all user data (cascade) | `/users/me`, `/users` | `user_service` | `/admin/users` |

### 33.3 Consistency Checklist

| Check | Result |
|---|---|
| Every table in Section 5 appears in the DDL (7.1), ORM (7.2), ER diagram (7.4) and data-flow tables (8). | Yes |
| Every endpoint in Section 18 maps to a service and a table or the agent (33.2). | Yes |
| Constraint and index names in the DDL match the SQLAlchemy naming convention. | Yes |
| Agent state fields (`AgentState`) match the adaptive rules (Section 15) and the stored JSON (`learning_sessions.agent_state`). | Yes |
| Assessment fields match `EvaluationResult` and the `learner_assessments` columns (`resolves_goal` is derived from `new_state.resolved`). | Yes |
| The example in Section 23 uses the formulas of Section 15 (values: p 0.355, 0.855, 0.9275; S 0.304, 0.397, 0.485; session score 0.6625). | Yes |
| The agent has no database access. The service layer saves all results in one transaction. | Yes |
| RAG can be off (`RAG_ENABLED=false`) without a change in the API or the schema. | Yes |
| Only one agent exists. The ten capabilities are modules of `SocraticAgent`. | Yes |

### 33.4 Additions to the Suggested Fields

| Table | Added column | Reason |
|---|---|---|
| `users` | `is_active` | Disable accounts without deleting data. |
| `learner_profiles` | `level_score`, `assessment_count` | Stable, explainable level estimate with hysteresis. |
| `subjects` | `is_active` | Retire a subject and keep history. |
| `learning_sessions` | `agent_state`, `summary` | Persist the agent state and the final summary. |
| `messages` | `retrieved_chunk_ids` | Audit of RAG use and hallucination analysis. |
| `learner_assessments` | `resolves_goal` | Record when an answer reached the goal. |
| `knowledge_documents` | `content_hash`, `status`, `error_message`, `uploaded_by` | Duplicate check, ingestion state, error report, accountability. |

### 33.5 Open Decisions

| ID | Question | Default in this document |
|---|---|---|
| OD-01 | Does the project proposal define other subjects, scoring rules or UI details? | This document uses the rules in Sections 14 to 16. Update them to match the proposal. |
| OD-02 | Which LLM provider and model will production use? | Configurable. Decide after the first evaluation run. |
| OD-03 | Can minors use the system? | Not decided. A legal review of children's data rules is necessary before release if they can. |
| OD-04 | Should students see numeric scores? | The API returns scores. The MVP UI shows feedback text, level and difficulty only. |
| OD-05 | What is the data retention period for sessions? | Not defined. Decide before launch. |
| OD-06 | Will production need more than one backend instance? | Not in the MVP. Then move the FAISS index to a dedicated retrieval service or use `pgvector` (Section 28.6). |

*End of document.*

---

*[Index](README.md) | [← Previous](17-developer-guide.md)*
