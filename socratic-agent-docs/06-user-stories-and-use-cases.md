# User Stories and Use Cases

*Socratic Agent project document. [Index](README.md) | [← Previous](05-requirements.md) | [Next →](07-socratic-agent.md)*

---

## 12. User Stories

| ID | Story | Acceptance criteria |
|---|---|---|
| US-01 | As a visitor, I want to create an account so that I can save my learning. | A valid form creates the account and shows the login page. A duplicate email shows an error. The password rules show before submit. |
| US-02 | As a student, I want to log in so that I can continue my learning. | Correct data opens the dashboard. Wrong data shows one generic error. The session survives a page reload. |
| US-03 | As a student, I want to stay logged in safely so that I do not log in every few minutes. | The system refreshes the access token without a visible action. Logout removes the cookies. |
| US-04 | As a student, I want to choose a subject so that the tutor uses the correct material. | The list shows active subjects. I can start a session from a subject card. |
| US-05 | As a student, I want to ask a question so that I can start learning a topic. | The first message creates the topic. The agent answers with a guiding question. The session title shows the topic. |
| US-06 | As a student, I want the tutor to ask me questions so that I think by myself. | The agent reply has a question. The agent reply does not state the final answer. |
| US-07 | As a student, I want to ask for a hint so that I can continue when I am stuck. | The hint button gives a hint. Each hint gives a little more help. No hint states the final answer. |
| US-08 | As a student, I want feedback on my answer so that I know what to improve. | After each answer I see short feedback. A wrong belief gets a clear but gentle correction question. |
| US-09 | As a student, I want the questions to match my level so that I am not bored or lost. | After good answers, questions become harder. After weak answers, questions become easier and hints increase. |
| US-10 | As a student, I want the tutor to use course material so that the content is correct. | With RAG on, the agent uses the retrieved material. The agent does not invent facts that the material contradicts. |
| US-11 | As a student, I want to end a session and see a summary so that I can review what I learned. | The summary shows concepts, strengths, corrected misconceptions, areas to review and next steps. |
| US-12 | As a student, I want to see my progress so that I stay motivated. | The dashboard shows my level, mastery per subject, topics attempted and mastered, strengths and weaknesses. |
| US-13 | As a student, I want to read my past sessions so that I can review them. | The history lists sessions with filters. I can open a session and read all messages and the summary. |
| US-14 | As a student, I want to delete my account so that my data is removed. | After confirmation, all my data is deleted. I cannot log in again. |
| US-15 | As an administrator, I want to manage subjects so that students can choose from current topics. | I can create, edit and retire a subject. A subject with history cannot be deleted. |
| US-16 | As an administrator, I want to upload course documents so that the tutor uses trusted material. | I can upload PDF, TXT or MD files. I see the processing status. Duplicate files are rejected. |
| US-17 | As an administrator, I want to test retrieval so that I can check document quality. | I enter a query and see the top chunks with scores. |
| US-18 | As an administrator, I want to disable an account so that I can stop misuse. | A disabled user cannot log in or use tokens. Data stays. |
| US-19 | As a developer, I want a fake LLM gateway so that I can test without cost. | Tests run without network access to an LLM. |
| US-20 | As a product owner, I want quality metrics so that I know if the tutor works. | The evaluation suite reports the metrics in Section 25. |

---

## 13. Use Cases

### UC-01 Register

| Item | Description |
|---|---|
| Actor | Visitor |
| Preconditions | None |
| Trigger | The visitor submits the registration form. |
| Main flow | 1. The system validates name, email and password. 2. The system checks that the email is new. 3. The system hashes the password. 4. The system creates `users` and `learner_profiles` rows. 5. The system returns `201` with the user. |
| Alternative flows | A1. Invalid data: `422` with field errors. A2. Email exists: `409 CONFLICT`. |
| Postconditions | A student account and a learner profile exist. |

### UC-02 Login

| Item | Description |
|---|---|
| Actor | Student or Administrator |
| Preconditions | The account exists and is active. |
| Trigger | The user submits email and password. |
| Main flow | 1. The system finds the user by email. 2. The system verifies the password hash. 3. The system creates an access token and a refresh token. 4. The BFF saves the tokens in httpOnly cookies. 5. The UI opens the dashboard. |
| Alternative flows | A1. Wrong data or inactive account: `401`. A2. Too many attempts: `429`. |
| Postconditions | The user is authenticated. |

### UC-03 Start Learning Session

| Item | Description |
|---|---|
| Actor | Student |
| Preconditions | The student is logged in. At least one active subject exists. |
| Trigger | The student selects a subject and chooses "Start session". |
| Main flow | 1. The system checks that the subject is active. 2. The system creates a `learning_sessions` row with status `active`. 3. The system increases `total_sessions` and `topics_attempted`. 4. The UI opens the chat screen. |
| Alternative flows | A1. Subject not found or retired: `404`. |
| Postconditions | An active session exists with the initial agent state. |

### UC-04 Ask Question

| Item | Description |
|---|---|
| Actor | Student |
| Preconditions | An active session exists and has no messages. |
| Trigger | The student sends the first message. |
| Main flow | 1. The system validates the message. 2. The agent sets the core question and the starting difficulty. 3. The system retrieves material (if RAG is on). 4. The agent creates a guiding question. 5. The system saves both messages and the session title. 6. The UI shows the agent message. |
| Alternative flows | A1. Empty or too long text: `422`. A2. LLM failure: `503`, nothing saved. |
| Postconditions | The session has one student `question` and one agent `guidance` message. |

### UC-05 Receive Socratic Guidance

| Item | Description |
|---|---|
| Actor | Student, Socratic Agent |
| Preconditions | An active session exists. |
| Trigger | The agent finishes a turn. |
| Main flow | 1. The agent builds the prompt from state, memory and retrieved material. 2. The LLM creates a reply. 3. The answer-leak guard checks the reply. 4. The system shows the reply. |
| Alternative flows | A1. The guard rejects the reply. The agent retries once, then uses a template question. A2. The student asks for a hint: the agent gives a hint at the next hint level. |
| Postconditions | The student sees a guiding question or a hint. |

### UC-06 Submit Response

| Item | Description |
|---|---|
| Actor | Student |
| Preconditions | The agent asked a question. |
| Trigger | The student sends an answer. |
| Main flow | 1. The system validates the message. 2. The system runs UC-07 (evaluate). 3. The system runs UC-08 (continue) or ends the goal. |
| Alternative flows | A1. The session is not active: `409`. A2. Two requests at the same time: `409 TURN_CONFLICT`. |
| Postconditions | The answer is saved with an assessment. |

### UC-07 Evaluate Response

| Item | Description |
|---|---|
| Actor | Socratic Agent |
| Preconditions | The student sent a `response` message. |
| Trigger | The system receives the message. |
| Main flow | 1. The evaluator builds the evaluation prompt. 2. The LLM returns scores, misconception and feedback. 3. The misconception detector normalizes the label. 4. The adaptive controller updates difficulty, hint level and streaks. 5. The level estimator updates the level score. 6. The agent checks if the goal is reached. |
| Alternative flows | A1. Invalid output: retry once, then `503`. |
| Postconditions | An assessment and a new agent state exist (saved with the turn). |

### UC-08 Continue Learning

| Item | Description |
|---|---|
| Actor | Student, Socratic Agent |
| Preconditions | The goal is not reached. |
| Trigger | The evaluation finishes. |
| Main flow | 1. The agent selects mode `ask`, `hint` or `worked_analogy`. 2. The agent retrieves material and builds the prompt. 3. The LLM creates the next question or hint. 4. The system saves the turn. |
| Postconditions | The dialogue continues at the adjusted difficulty and hint level. |

### UC-09 End Session

| Item | Description |
|---|---|
| Actor | Student |
| Preconditions | The session is active. |
| Trigger | The student selects "End session", or the UI ends the session after the goal is reached. |
| Main flow | 1. The system loads messages and assessments. 2. The summarizer creates the summary. 3. The system sets status (`completed` if the goal was reached, otherwise `abandoned`). 4. The system updates mastery and the learner profile. 5. The UI shows the summary. |
| Alternative flows | A1. LLM failure: the system uses a fallback summary. A2. Session already ended: `409`. |
| Postconditions | The session is closed. Progress and summary are saved. |

### UC-10 View Progress

| Item | Description |
|---|---|
| Actor | Student |
| Preconditions | The student is logged in. |
| Trigger | The student opens the progress page. |
| Main flow | 1. The system reads the profile and progress rows. 2. The UI shows level, mastery per subject, topics, strengths, weaknesses and recent sessions. |
| Postconditions | None (read only). |

### UC-11 Manage Educational Documents

| Item | Description |
|---|---|
| Actor | Administrator |
| Preconditions | The administrator is logged in. The subject exists. |
| Trigger | The administrator uploads, re-indexes or deletes a document. |
| Main flow (upload) | 1. The system validates type and size. 2. The system computes the SHA-256 hash and rejects a duplicate. 3. The system saves the document row (`pending`) and returns `202`. 4. A background task extracts text, creates chunks, creates embeddings and saves them. 5. The status changes to `indexed`. |
| Alternative flows | A1. Unsupported type: `415`. A2. File too large: `413`. A3. Processing error: status `failed` with `error_message`. A4. Delete: the system removes vectors first, then the rows. |
| Postconditions | The document is searchable (`indexed`) or marked `failed`. |

---

*[Index](README.md) | [← Previous](05-requirements.md) | [Next →](07-socratic-agent.md)*
