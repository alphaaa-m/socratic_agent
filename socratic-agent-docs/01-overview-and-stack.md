# Project Overview and Technology Stack

*Socratic Agent project document. [Index](README.md) | [Next →](02-architecture-and-ai-flow.md)*

---

## 1. Project Overview

### 1.1 Purpose

The Socratic Agent is an AI-powered educational system. It helps students learn through **guided questioning**. It does not give the final answer. It asks questions, gives hints, checks the student's reasoning, and adapts to the student's level.

### 1.2 Problem Statement

Many AI tools give a complete answer at once. A student can copy the answer and learn nothing. The student does not practice reasoning. The teacher cannot see where the student has a wrong belief.

### 1.3 Goals

| ID | Goal |
|---|---|
| G-01 | Help the student reach the correct reasoning through the student's own thinking. |
| G-02 | Find wrong beliefs (misconceptions) early and correct them with questions. |
| G-03 | Match question difficulty and hint size to the student's level. |
| G-04 | Use trusted course material to keep answers accurate (RAG). |
| G-05 | Record sessions and progress so the student can review learning. |
| G-06 | Give the student a clear summary at the end of each session. |

### 1.4 System Capabilities

The system must:

1. Ask guiding Socratic questions.
2. Give hints when the student needs them.
3. Evaluate student responses.
4. Detect misconceptions and reasoning quality.
5. Estimate the learner's level.
6. Adapt the difficulty and the amount of guidance.
7. Retrieve relevant educational material with RAG.
8. Track learning sessions and progress.
9. Summarize the student's learning at the end of a session.

### 1.5 Scope

| In scope | Out of scope (first release) |
|---|---|
| Web application for students | Native mobile application |
| Administrator tools for subjects and documents | Teacher dashboard |
| Text-based Socratic dialogue | Voice and video interaction |
| One Socratic Agent | Multiple independent agents |
| RAG with uploaded course documents (PDF, TXT, MD) | Web crawling, image and table understanding |
| Progress tracking per subject | Formal grading and certification |

### 1.6 Assumptions and Constraints

| ID | Statement |
|---|---|
| A-01 | The project proposal was not attached to the request. This document uses the concept and core workflow as described in the request. Change the document if the proposal differs. |
| A-02 | The student uses a modern web browser and has an internet connection. |
| A-03 | One tutoring session covers one learning goal (topic). |
| A-04 | An external LLM API is available (Groq or Gemini; OpenAI/Anthropic also supported). |
| A-05 | Course documents are text-based and in a language the LLM supports. |
| C-01 | The stack in Section 2 is fixed. |
| C-02 | The architecture uses one agent. |
| C-03 | The agent must not give the final answer directly (see Section 14.6). |

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui | Web UI and BFF route handlers |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.x, Pydantic v2 | REST API, business logic, validation |
| Database | PostgreSQL 15+ with SQLAlchemy ORM, Alembic | Persistent data and migrations |
| Authentication | JWT (access and refresh tokens), Argon2 password hashing | Identity and access control |
| AI layer | LangChain, LLM API (Groq or Gemini; OpenAI/Anthropic also supported) | Language model access |
| RAG | HuggingFace sentence embeddings (`sentence-transformers`), **FAISS** (vectors), PostgreSQL (chunk text) | Retrieval of course material |
| Development | Git, GitHub, GitHub Actions, `uv` (Python packages) | Version control and CI |
| Deployment | Vercel (Next.js), Railway or Render (FastAPI), managed PostgreSQL | Hosting |

### 2.1 Technology Decisions

| ID | Decision | Reason |
|---|---|---|
| D-01 | Use **synchronous** SQLAlchemy sessions and synchronous FastAPI route functions. | FastAPI runs them in a thread pool. This keeps the code simple. The LLM call is the slow part. |
| D-02 | Use **UUID** primary keys. | IDs are safe to expose in URLs. IDs do not show record counts. |
| D-03 | Use `VARCHAR` with `CHECK` constraints for enumerations. | Alembic changes are simple. No PostgreSQL enum type migration is necessary. |
| D-04 | Use **FAISS** as the vector index. Hide it behind a `VectorStore` interface. | FAISS is fast and simple. It stores only vectors, so chunk text and metadata stay in PostgreSQL (the source of truth). |
| D-05 | Use `argon2-cffi` for password hashing. | Argon2id is a modern, recommended algorithm. |
| D-06 | Use a **BFF** in Next.js. The browser never sees the JWT. | httpOnly cookies protect tokens from JavaScript (XSS). |
| D-07 | Put all LLM calls behind an `LLMGateway` interface. | Tests use a fake gateway. The provider can change without agent changes. |
| D-08 | The agent is a **pure component**: it does not read or write the database. | The service layer owns persistence. The agent is easy to test. |

---

*[Index](README.md) | [Next →](02-architecture-and-ai-flow.md)*
