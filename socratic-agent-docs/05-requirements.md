# Requirements and User Roles

*Socratic Agent project document. [Index](README.md) | [← Previous](04-database-schema.md) | [Next →](06-user-stories-and-use-cases.md)*

---

## 9. Functional Requirements

Priority: **M** = in the MVP. **L** = later release.

### 9.1 User Registration (REG)

| ID | Requirement | Pri |
|---|---|---|
| FR-REG-01 | The system must let a visitor create a student account with name, email and password. | M |
| FR-REG-02 | The system must reject an email that already exists (`409`). | M |
| FR-REG-03 | The system must convert the email to lowercase before it saves the email. | M |
| FR-REG-04 | The system must require a password of 8 to 128 characters with at least one letter and one digit. | M |
| FR-REG-05 | The system must create a `learner_profiles` row in the same transaction as the user. | M |
| FR-REG-06 | The system must set the role to `student`. Only an administrator can create or promote an administrator. | M |

### 9.2 User Login (LOG)

| ID | Requirement | Pri |
|---|---|---|
| FR-LOG-01 | The system must authenticate a user with email and password. | M |
| FR-LOG-02 | The system must return the same error for an unknown email and a wrong password. | M |
| FR-LOG-03 | The system must refuse login for an account with `is_active = false`. | M |
| FR-LOG-04 | The system must limit login attempts to 5 per minute for each IP address and email. | M |

### 9.3 JWT Authentication (JWT)

| ID | Requirement | Pri |
|---|---|---|
| FR-JWT-01 | The system must issue an access token (30 minutes) and a refresh token (7 days) after login. | M |
| FR-JWT-02 | The system must sign tokens with `HS256` and a secret of at least 32 bytes. | M |
| FR-JWT-03 | Each token must contain `sub`, `type`, `iat`, `exp` and `jti`. | M |
| FR-JWT-04 | The system must accept only `access` tokens for API calls and only `refresh` tokens for `/auth/refresh`. | M |
| FR-JWT-05 | The system must load the user from the database for each request. It must not trust the role claim in the token. | M |
| FR-JWT-06 | The system must return `401` for an expired, invalid or wrong-type token. | M |

### 9.4 Subject Selection (SUB)

| ID | Requirement | Pri |
|---|---|---|
| FR-SUB-01 | The system must show the list of active subjects. | M |
| FR-SUB-02 | The student must select one subject to start a session. | M |
| FR-SUB-03 | An administrator must be able to create, change and retire subjects. | M |
| FR-SUB-04 | The system must not delete a subject that has sessions or documents. | M |

### 9.5 Starting a Tutoring Session (SES)

| ID | Requirement | Pri |
|---|---|---|
| FR-SES-01 | The system must create a session with status `active` for the selected subject. | M |
| FR-SES-02 | The system must set initial `agent_state` values from the learner level. | M |
| FR-SES-03 | The system must increase `total_sessions` and `topics_attempted` when a session starts. | M |
| FR-SES-04 | The system must set the session title from the first question (maximum 60 characters). | M |
| FR-SES-05 | The system must not accept messages in a session that is not `active` (`409`). | M |

### 9.6 Sending Questions (MSG)

| ID | Requirement | Pri |
|---|---|---|
| FR-MSG-01 | The system must accept a student message of 1 to 4000 characters. | M |
| FR-MSG-02 | The system must save the first student message as `question` and later messages as `response`. | M |
| FR-MSG-03 | The system must allow only the session owner to send messages. | M |
| FR-MSG-04 | The system must return the agent response in the same HTTP response. | M |
| FR-MSG-05 | The system must limit each user to 20 messages per minute. | M |

### 9.7 Receiving Socratic Guidance (SOC)

| ID | Requirement | Pri |
|---|---|---|
| FR-SOC-01 | The agent must respond with a guiding question or a hint. | M |
| FR-SOC-02 | The agent must not state the final answer to the core question. | M |
| FR-SOC-03 | Each agent message must be short (maximum 120 words) and must contain at least one question. | M |
| FR-SOC-04 | The agent must use the student's own words and reasoning when it asks the next question. | M |
| FR-SOC-05 | If the student asks for the answer, the agent must refuse politely and offer a hint. | M |
| FR-SOC-06 | When the student reaches the correct reasoning, the agent must confirm it and tell the student that the session can end. | M |

### 9.8 Answer Evaluation (EVA)

| ID | Requirement | Pri |
|---|---|---|
| FR-EVA-01 | The system must evaluate each student response after the first message. | M |
| FR-EVA-02 | The evaluation must give `correctness_score`, `reasoning_score` and `confidence_score` from 0 to 1. | M |
| FR-EVA-03 | The evaluation must give a misconception label or `null`. | M |
| FR-EVA-04 | The system must save one `learner_assessments` row for each evaluated message. | M |
| FR-EVA-05 | The system must give the student short feedback with each response. | M |
| FR-EVA-06 | If the evaluation output is not valid, the system must repeat the LLM call once. If it fails again, the system must return `503` and save nothing. | M |

### 9.9 Adaptive Difficulty (ADP)

| ID | Requirement | Pri |
|---|---|---|
| FR-ADP-01 | The system must keep a difficulty from 1 to 5 for each session. | M |
| FR-ADP-02 | The system must increase the difficulty after two consecutive high-performance turns. | M |
| FR-ADP-03 | The system must decrease the difficulty after two consecutive low-performance turns. | M |
| FR-ADP-04 | The system must update the learner level estimate after each assessment. | M |
| FR-ADP-05 | The system must change the learner level only after 5 or more assessments and with hysteresis (Section 15). | M |

### 9.10 Hint Generation (HNT)

| ID | Requirement | Pri |
|---|---|---|
| FR-HNT-01 | The system must support hint levels 0 to 3. | M |
| FR-HNT-02 | The system must increase the hint level when the student asks for a hint (button or text). | M |
| FR-HNT-03 | The system must increase the hint level after two consecutive low-performance turns. | M |
| FR-HNT-04 | The system must decrease the hint level after a high-performance turn. | M |
| FR-HNT-05 | A hint must not contain the final answer, even at level 3. | M |

### 9.11 RAG Retrieval (RAG)

| ID | Requirement | Pri |
|---|---|---|
| FR-RAG-01 | The system must find chunks that are relevant to the core question and the latest student message. | L |
| FR-RAG-02 | The system must search only chunks of the session's subject. | L |
| FR-RAG-03 | The system must return at most `RAG_TOP_K` chunks with a score of at least `RAG_MIN_SCORE`. | L |
| FR-RAG-04 | The system must save the IDs of the used chunks in `messages.retrieved_chunk_ids`. | L |
| FR-RAG-05 | If there are no relevant chunks, the agent must work in general knowledge mode. | L |
| FR-RAG-06 | The system must keep working if RAG is disabled (`RAG_ENABLED=false`). | M |

### 9.12 Conversation History (CNV)

| ID | Requirement | Pri |
|---|---|---|
| FR-CNV-01 | The system must save every message of a session. | M |
| FR-CNV-02 | The system must return the messages of a session in time order with pagination. | M |
| FR-CNV-03 | The system must let a student open a past session and read its messages. | M |

### 9.13 Progress Tracking (PRG)

| ID | Requirement | Pri |
|---|---|---|
| FR-PRG-01 | The system must keep a mastery score (0 to 1) for each user and subject. | M |
| FR-PRG-02 | The system must update mastery when a session ends as `completed` (Section 15.6). | M |
| FR-PRG-03 | The system must count `topics_attempted` and `topics_mastered`. | M |
| FR-PRG-04 | The system must show the learner level, strengths and weaknesses to the student. | M |
| FR-PRG-05 | The system must show a score trend for the last sessions of a subject. | L |

### 9.14 Session Summaries (SUM)

| ID | Requirement | Pri |
|---|---|---|
| FR-SUM-01 | The system must create a structured summary when a session ends. | M |
| FR-SUM-02 | The summary must list key concepts, strengths, corrected misconceptions, areas to review and next steps. | M |
| FR-SUM-03 | If the LLM fails, the system must still end the session and create a fallback summary from stored data. | M |
| FR-SUM-04 | The system must save the summary in `learning_sessions.summary` and as a `summary` message. | M |

### 9.15 Learning History (HIS)

| ID | Requirement | Pri |
|---|---|---|
| FR-HIS-01 | The system must list the sessions of the student (newest first) with filters for subject and status. | M |
| FR-HIS-02 | The system must show the summary of each completed session. | M |
| FR-HIS-03 | The system must let the student see the assessments of a session. | M |

### 9.16 Knowledge Document Management (DOC)

| ID | Requirement | Pri |
|---|---|---|
| FR-DOC-01 | An administrator must be able to upload PDF, TXT and MD files (maximum 10 MB) for a subject. | L |
| FR-DOC-02 | The system must reject duplicate files for the same subject (same SHA-256). | L |
| FR-DOC-03 | The system must process uploads in the background (extract, chunk, embed, index) and show the status. | L |
| FR-DOC-04 | An administrator must be able to list, view, re-index and delete documents. | L |
| FR-DOC-05 | The system must delete the vectors of a document before it deletes the document. | L |
| FR-DOC-06 | An administrator must be able to test retrieval with a search query. | L |

### 9.17 Account and Privacy (ACC)

| ID | Requirement | Pri |
|---|---|---|
| FR-ACC-01 | A user must be able to read and change the user's own name and password. | M |
| FR-ACC-02 | A user must be able to delete the user's own account. The system must delete all personal learning data. | M |
| FR-ACC-03 | An administrator must be able to list users, change roles and disable accounts. | M |

---

## 10. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-PERF-01 | Performance | A non-AI API request (login, list, read) must complete in 300 ms or less at the 95th percentile. |
| NFR-PERF-02 | Performance | A tutoring turn (two LLM calls) should complete in 8 seconds or less at the 95th percentile. The hard timeout is 30 seconds for each LLM call. |
| NFR-PERF-03 | Performance | Retrieval from the vector store must complete in 300 ms or less at the 95th percentile. |
| NFR-PERF-04 | Performance | The first page of the chat UI must load in 2.5 seconds or less (LCP) on a normal broadband connection. |
| NFR-SCAL-01 | Scalability | The backend must be stateless, except for the local vector store. It must scale to several instances after the vector store moves to a server (Section 28.6). |
| NFR-SCAL-02 | Scalability | The MVP must support 100 concurrent active sessions. |
| NFR-SCAL-03 | Scalability | The system must not hold a database connection during an LLM call. |
| NFR-SEC-01 | Security | The system must hash passwords with Argon2id. |
| NFR-SEC-02 | Security | The system must use HTTPS for all external traffic. |
| NFR-SEC-03 | Security | The system must enforce authorization on every endpoint (Section 11, 26). |
| NFR-SEC-04 | Security | The LLM API key must stay on the server. The browser must never receive it. |
| NFR-REL-01 | Reliability | The system must save a turn completely or not at all (one transaction). |
| NFR-REL-02 | Reliability | The system must retry LLM calls two times with exponential backoff for timeouts, `429` and `5xx` errors. |
| NFR-REL-03 | Reliability | The system must create a daily database backup and keep it for 7 days or more. |
| NFR-MNT-01 | Maintainability | The backend must have a layered structure (API, services, agent, RAG, database). |
| NFR-MNT-02 | Maintainability | Unit test coverage for `services` and `agents` should be 80% or more. |
| NFR-MNT-03 | Maintainability | The code must pass `ruff` (Python) and `eslint` and `tsc` (TypeScript) in CI. |
| NFR-MNT-04 | Maintainability | All database changes must use Alembic migrations. |
| NFR-USE-01 | Usability | The chat UI must work on screens from 360 px wide. |
| NFR-USE-02 | Usability | The UI must meet WCAG 2.1 AA for contrast, keyboard use and screen-reader labels. |
| NFR-USE-03 | Usability | The UI must show a loading state while the agent responds. |
| NFR-AVL-01 | Availability | The monthly availability target for the API is 99.5%. |
| NFR-AVL-02 | Availability | The system must have a health endpoint for monitoring. |
| NFR-AVL-03 | Availability | If the vector store fails, tutoring must continue in general knowledge mode. |
| NFR-PRV-01 | Privacy | The system must not send email, password data or other direct identifiers to the LLM. |
| NFR-PRV-02 | Privacy | The system must delete all personal data when the user deletes the account. |
| NFR-PRV-03 | Privacy | The logs must not contain passwords, tokens, API keys or full message text. |
| NFR-AI-01 | AI response quality | The rate of final-answer leaks must be 2% or less on the test set (Section 25). |
| NFR-AI-02 | AI response quality | At least 95% of agent replies must contain a guiding question. |
| NFR-AI-03 | AI response quality | The hallucination rate with RAG should be 5% or less on the test set. |
| NFR-AI-04 | AI response quality | The agent must use temperature 0 for evaluation and 0.3 or less for tutor replies. |

---

## 11. User Roles

### 11.1 Roles

| Role | Description |
|---|---|
| **Student** | A learner. The student uses the tutoring features and sees only the student's own data. |
| **Administrator** | A staff user. The administrator manages subjects, documents and users. |

A **Teacher** role is a future enhancement (Section 31).

### 11.2 Permission Matrix

Legend: **Own** = only the user's own records. **All** = all records. **-** = not allowed.

| Resource / action | Student | Administrator |
|---|---|---|
| Register, login, refresh | Yes | Yes |
| Read and change own account | Own | Own |
| Delete own account | Own | Own |
| List users, change role, disable user | - | All |
| List subjects | Yes | Yes |
| Create, change, retire subjects | - | Yes |
| Create a learning session | Own | Own |
| Read sessions and messages | Own | - (see note) |
| Send message, request hint, end session | Own | Own |
| Read assessments | Own | - |
| Read progress and learner profile | Own | - |
| Upload, list, re-index, delete documents | - | Yes |
| Test retrieval (`/documents/search`) | - | Yes |
| Health endpoint | Public | Public |

**Note:** administrators cannot read student conversations in the MVP. This limits access to personal data. A future teacher or support role can get this access with explicit consent.

---

*[Index](README.md) | [← Previous](04-database-schema.md) | [Next →](06-user-stories-and-use-cases.md)*
