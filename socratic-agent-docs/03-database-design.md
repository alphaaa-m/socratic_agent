# Database Design, Relationships and Data Flow

*Socratic Agent project document. [Index](README.md) | [← Previous](02-architecture-and-ai-flow.md) | [Next →](04-database-schema.md)*

---

## 5. Database Design

### 5.1 Database Overview

| Item | Value |
|---|---|
| DBMS | PostgreSQL 15 or newer |
| Access layer | SQLAlchemy 2.x ORM (synchronous), Alembic migrations |
| Primary keys | `UUID`, default `gen_random_uuid()` (built in since PostgreSQL 13) |
| Timestamps | `TIMESTAMPTZ`, stored in UTC, default `now()` |
| Enumerations | `VARCHAR(20)` with named `CHECK` constraints |
| Flexible data | `JSONB` for preferences, strengths, weaknesses, agent state and summary |
| Scores | `NUMERIC(4,3)` with range `0.000` to `1.000` |
| Naming | Tables: plural `snake_case`. Constraints: `pk_`, `fk_`, `uq_`, `ck_`, `ix_` prefixes |
| Vector data | **Not** in PostgreSQL. The vector store holds embeddings (Section 17) |

Columns marked with **†** are additions to the suggested field list. Each addition has a stated reason.

### 5.2 Entity Identification

| Entity | Table | Purpose |
|---|---|---|
| User | `users` | Account, credentials and role |
| Learner profile | `learner_profiles` | Learner level and learning state |
| Subject | `subjects` | Learning area (for example, "Python Programming") |
| Learning session | `learning_sessions` | One tutoring conversation |
| Message | `messages` | One chat message |
| Learner assessment | `learner_assessments` | Evaluation of one student message |
| Learning progress | `learning_progress` | Mastery of one subject for one user |
| Knowledge document | `knowledge_documents` | Metadata of a RAG source document |
| Document chunk | `document_chunks` | One text chunk of a document |

### 5.3 Conventions

- A **topic** is one learning session. The session `title` holds the topic text.
- `topics_attempted` increases when a session starts.
- `topics_mastered` increases when a session ends as `completed` with a session score of 0.75 or higher.
- The first student message of a session has `message_type = 'question'`. Later student messages have `message_type = 'response'`.
- A `learner_assessments` row always points to a **student** message.

### 5.4 Table Definitions

#### 5.4.1 `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | User identifier |
| name | VARCHAR(120) | NOT NULL | Display name |
| email | VARCHAR(255) | NOT NULL, UNIQUE, `CHECK (email = lower(email))` | Login name. The application converts it to lowercase |
| password_hash | VARCHAR(255) | NOT NULL | Argon2id hash. Never the password |
| role | VARCHAR(20) | NOT NULL, default `'student'`, `CHECK IN ('student','admin')` | Access role |
| is_active † | BOOLEAN | NOT NULL, default `TRUE` | Administrator can disable an account without deleting data |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()` | Last change time |

#### 5.4.2 `learner_profiles`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | Profile identifier |
| user_id | UUID | NOT NULL, UNIQUE, FK → `users.id` ON DELETE CASCADE | Owner (one profile per user) |
| current_level | VARCHAR(20) | NOT NULL, default `'beginner'`, `CHECK IN ('beginner','intermediate','advanced')` | Estimated learner level |
| level_score † | NUMERIC(4,3) | NOT NULL, default `0.300`, `CHECK BETWEEN 0 AND 1` | Smoothed skill estimate. Input for the level decision |
| assessment_count † | INTEGER | NOT NULL, default `0`, `CHECK >= 0` | Number of assessments in the estimate. Level changes need at least 5 |
| learning_preferences | JSONB | NOT NULL, default `'{}'` | Student preferences (for example, `{"language":"en","hint_style":"short"}`) |
| strengths | JSONB | NOT NULL, default `'[]'` | List of `{"label","last_seen_at"}` objects. Maximum 10 |
| weaknesses | JSONB | NOT NULL, default `'[]'` | List of `{"label","count","last_seen_at"}` objects. Maximum 10 |
| total_sessions | INTEGER | NOT NULL, default `0`, `CHECK >= 0` | Number of sessions started |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()` | Last change time |

#### 5.4.3 `subjects`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | Subject identifier |
| name | VARCHAR(120) | NOT NULL, UNIQUE | Subject name |
| description | TEXT | NULL | Subject description |
| is_active † | BOOLEAN | NOT NULL, default `TRUE` | Retire a subject without deleting its history |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Creation time |

#### 5.4.4 `learning_sessions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | Session identifier |
| user_id | UUID | NOT NULL, FK → `users.id` ON DELETE CASCADE | Student |
| subject_id | UUID | NOT NULL, FK → `subjects.id` ON DELETE RESTRICT | Subject |
| title | VARCHAR(255) | NOT NULL, default `'New session'` | Topic text. The first question sets it |
| status | VARCHAR(20) | NOT NULL, default `'active'`, `CHECK IN ('active','completed','abandoned')` | Session state |
| agent_state † | JSONB | NOT NULL, default `'{}'` | State of the agent (difficulty, hint level, streaks, turn counter) |
| summary † | JSONB | NULL | Structured session summary. Set at the end |
| started_at | TIMESTAMPTZ | NOT NULL, default `now()` | Start time |
| ended_at | TIMESTAMPTZ | NULL | End time. `NULL` while `active` |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Row creation time |

Table checks: `(status = 'active') = (ended_at IS NULL)` and `ended_at IS NULL OR ended_at >= started_at`.

#### 5.4.5 `messages`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | Message identifier |
| session_id | UUID | NOT NULL, FK → `learning_sessions.id` ON DELETE CASCADE | Session |
| sender | VARCHAR(10) | NOT NULL, `CHECK IN ('student','agent','system')` | Author |
| content | TEXT | NOT NULL, `CHECK (char_length(content) > 0)` | Message text |
| message_type | VARCHAR(20) | NOT NULL, `CHECK IN ('question','response','guidance','hint','summary','system')` | Message kind |
| retrieved_chunk_ids † | JSONB | NOT NULL, default `'[]'` | IDs of chunks used for this agent message (for audit and evaluation) |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Creation time |

Table check: student → `question` or `response`; agent → `guidance`, `hint` or `summary`; system → `system`.

#### 5.4.6 `learner_assessments`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | Assessment identifier |
| session_id | UUID | NOT NULL, FK → `learning_sessions.id` ON DELETE CASCADE | Session |
| message_id | UUID | NOT NULL, UNIQUE, FK → `messages.id` ON DELETE CASCADE | The evaluated student message |
| correctness_score | NUMERIC(4,3) | NOT NULL, `CHECK BETWEEN 0 AND 1` | Factual correctness |
| reasoning_score | NUMERIC(4,3) | NOT NULL, `CHECK BETWEEN 0 AND 1` | Quality of reasoning |
| confidence_score | NUMERIC(4,3) | NOT NULL, `CHECK BETWEEN 0 AND 1` | Confidence that the student shows in the text |
| difficulty_level | SMALLINT | NOT NULL, `CHECK BETWEEN 1 AND 5` | Difficulty of the question that the student answered |
| misconception | TEXT | NULL | Normalized misconception label. `NULL` if none |
| feedback | TEXT | NULL | Short feedback for the student |
| resolves_goal † | BOOLEAN | NOT NULL, default `FALSE` | `TRUE` if the answer reaches the core goal |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Creation time |

#### 5.4.7 `learning_progress`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | Progress identifier |
| user_id | UUID | NOT NULL, FK → `users.id` ON DELETE CASCADE | Student |
| subject_id | UUID | NOT NULL, FK → `subjects.id` ON DELETE CASCADE | Subject |
| mastery_score | NUMERIC(4,3) | NOT NULL, default `0`, `CHECK BETWEEN 0 AND 1` | Mastery of the subject |
| topics_attempted | INTEGER | NOT NULL, default `0`, `CHECK >= 0` | Sessions started in this subject |
| topics_mastered | INTEGER | NOT NULL, default `0`, `CHECK >= 0 AND <= topics_attempted` | Sessions completed with mastery |
| last_activity_at | TIMESTAMPTZ | NULL | Time of last activity |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()` | Last change time |

Unique constraint: (`user_id`, `subject_id`).

#### 5.4.8 `knowledge_documents`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | Document identifier |
| subject_id | UUID | NOT NULL, FK → `subjects.id` ON DELETE RESTRICT | Subject |
| title | VARCHAR(255) | NOT NULL | Document title |
| description | TEXT | NULL | Short description |
| file_name | VARCHAR(255) | NOT NULL | Original file name |
| source | VARCHAR(500) | NULL | Origin (URL, book, course) |
| content_hash † | CHAR(64) | NOT NULL | SHA-256 of the file. Prevents duplicate uploads |
| status † | VARCHAR(20) | NOT NULL, default `'pending'`, `CHECK IN ('pending','processing','indexed','failed')` | Ingestion state |
| error_message † | TEXT | NULL | Failure reason when `status = 'failed'` |
| uploaded_by † | UUID | NULL, FK → `users.id` ON DELETE SET NULL | Administrator who uploaded the file |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Creation time |

Unique constraint: (`subject_id`, `content_hash`).

#### 5.4.9 `document_chunks`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, NOT NULL, default `gen_random_uuid()` | Chunk identifier |
| vector_id † | BIGINT | NOT NULL, UNIQUE, `GENERATED ALWAYS AS IDENTITY` | Integer ID of the vector in FAISS (FAISS needs int64 IDs) |
| document_id | UUID | NOT NULL, FK → `knowledge_documents.id` ON DELETE CASCADE | Parent document |
| content | TEXT | NOT NULL | Chunk text |
| chunk_index | INTEGER | NOT NULL, `CHECK >= 0` | Position in the document |
| embedding_reference | VARCHAR(100) | NULL, UNIQUE | `str(vector_id)` after the chunk is indexed. `NULL` until indexed |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` | Creation time |

Unique constraint: (`document_id`, `chunk_index`).

---

## 6. Database Relationships

### 6.1 Relationship Tree

```text
User
 ├── LearnerProfile
 ├── LearningSessions
 ├── LearningProgress
 └── KnowledgeDocuments (as uploader, optional)

Subject
 ├── LearningSessions
 ├── LearningProgress
 └── KnowledgeDocuments

LearningSession
 ├── Messages
 └── LearnerAssessments

Message
 └── LearnerAssessment

KnowledgeDocument
 └── DocumentChunks
```

### 6.2 Cardinality

```text
User 1 ─── 1 LearnerProfile
User 1 ─── N LearningSessions
User 1 ─── N LearningProgress
User 0..1 ─── N KnowledgeDocuments        (uploaded_by)
Subject 1 ─── N LearningSessions
Subject 1 ─── N LearningProgress
Subject 1 ─── N KnowledgeDocuments
LearningSession 1 ─── N Messages
LearningSession 1 ─── N LearnerAssessments
Message 1 ─── 0..1 LearnerAssessment      (student messages only)
KnowledgeDocument 1 ─── N DocumentChunks
User N ─── N Subject                      (through LearningProgress)
```

### 6.3 Foreign Keys and Cascade Behavior

| Child table.column | Parent | ON DELETE | Reason |
|---|---|---|---|
| learner_profiles.user_id | users | CASCADE | Deleting a user must delete the profile. |
| learning_sessions.user_id | users | CASCADE | User deletion removes all personal learning data (privacy). |
| learning_sessions.subject_id | subjects | RESTRICT | The system must not lose session history. Administrators set `is_active = false` instead. |
| messages.session_id | learning_sessions | CASCADE | Messages have no meaning without the session. |
| learner_assessments.session_id | learning_sessions | CASCADE | Same reason. |
| learner_assessments.message_id | messages | CASCADE | An assessment belongs to one message. |
| learning_progress.user_id | users | CASCADE | Personal data. |
| learning_progress.subject_id | subjects | CASCADE | Progress is derived data. |
| knowledge_documents.subject_id | subjects | RESTRICT | The administrator must remove documents first (the service also removes vectors). |
| knowledge_documents.uploaded_by | users | SET NULL | Documents stay when the uploader account is deleted. |
| document_chunks.document_id | knowledge_documents | CASCADE | Chunks have no meaning without the document. |

> **Important:** a database cascade does **not** delete vectors. The service must delete the vectors of a document before it deletes the document row (Section 17.6).

---

## 8. Data Flow Between AI and Database

### 8.1 When the System Reads and Writes PostgreSQL

```text
Login
 → users

Start Session
 → learning_sessions
 → learner_profiles
 → learning_progress

Student Message
 → messages

Retrieve Learner State
 → learner_profiles
 → learning_progress

Evaluate Response
 → learner_assessments

Update Learning State
 → learner_profiles
 → learning_progress
 → learning_sessions (agent_state)

End Session
 → learning_sessions
 → messages
 → learning_progress
 → learner_profiles
```

| Event | Reads | Writes | Notes |
|---|---|---|---|
| Register | `users` (email check) | `users`, `learner_profiles` | One transaction. |
| Login | `users` | - | No write. |
| Start session | `subjects`, `learner_profiles` | `learning_sessions` (insert, `agent_state` with initial values), `learner_profiles.total_sessions` +1, `learning_progress` (upsert row, `topics_attempted` +1) | One transaction. |
| Student message (read phase) | `learning_sessions`, `messages` (last N), `learner_profiles`, `subjects` | - | Short transaction. It closes before the LLM calls. |
| Student message (write phase) | `learning_sessions` (row lock) | `messages` (student and agent), `learner_assessments`, `learning_sessions.agent_state` and `title`, `learner_profiles` (`level_score`, `assessment_count`, `current_level`), `learning_progress.last_activity_at` | One transaction. See 8.2. |
| Hint request (button) | Same as read phase | `messages` (agent hint), `learning_sessions.agent_state` | No assessment. |
| End session | `messages`, `learner_assessments`, `learning_progress` | `learning_sessions` (status, `ended_at`, `summary`), `messages` (summary), `learning_progress` (mastery, `topics_mastered`), `learner_profiles` (strengths, weaknesses) | Summary LLM call first, then one write transaction. |
| View progress | `learner_profiles`, `learning_progress`, `subjects` | - | - |
| View history | `learning_sessions`, `messages`, `learner_assessments` | - | - |
| Upload document | `knowledge_documents` (hash check) | `knowledge_documents`, `document_chunks` | Background task. Also writes to the vector store. |

### 8.2 Transaction and Concurrency Rules

1. The read phase loads data and closes the transaction.
2. The agent runs. It calls the LLM. No database connection is open.
3. The write phase starts a new transaction. It runs `SELECT ... FOR UPDATE` on the session row.
4. The service compares `agent_state.turn_index` with the value that it read in step 1. If the values differ, another request changed the session. The service rolls back and returns `409 TURN_CONFLICT`.
5. The service writes all rows and commits. If any write fails, nothing is saved. The student sends the message again.

### 8.3 PostgreSQL and FAISS: Who Stores What

| Information | PostgreSQL | FAISS index |
|---|---|---|
| Users, sessions, messages, assessments, progress | Yes | No |
| Document metadata (title, subject, status, hash) | Yes | No |
| Chunk text and chunk order | Yes (source of truth) | **No** |
| Embedding vector | **No** | Yes |
| Link between chunk and vector | `document_chunks.vector_id` (BIGINT) | The same number is the vector ID |
| Subject separation | `knowledge_documents.subject_id` | One index file for each subject |
| Which chunks the agent used | `messages.retrieved_chunk_ids` | No |

The rule: **PostgreSQL has the facts. FAISS has only vectors.** FAISS cannot store text or metadata. A retrieval therefore has two steps: FAISS returns `vector_id` values, and PostgreSQL returns the chunk text for those IDs (one short read-only query). If the two stores differ, PostgreSQL is correct and the system rebuilds the index (Section 17.6). A vector without a chunk row is ignored by the retriever.

---

*[Index](README.md) | [← Previous](02-architecture-and-ai-flow.md) | [Next →](04-database-schema.md)*
