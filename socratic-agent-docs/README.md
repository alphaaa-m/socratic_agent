# AI Project: Socratic Agent

## An AI-Powered Socratic Tutor

### Software Engineering Project Document (ASD-STE100-style)

| Item | Value |
|---|---|
| Document version | 1.0 |
| Date | 2026-10-07 |
| Status | Draft for implementation |
| Document type | Combined PRD, SRS, SDD, architecture, database, API, AI/RAG, developer, testing and deployment document |
| Main architecture | Next.js + FastAPI + PostgreSQL + LangChain + RAG + LLM |
| Agent model | One single Socratic Agent (no multi-agent design) |

---

## About This Document

### Purpose

This document describes one integrated system: the **Socratic Agent**. It gives developers all the information they need to design, build, test, deploy and operate the system.

### Which Section Serves Which Document Role

| Document role | Sections |
|---|---|
| Project Requirement Document | 1, 11, 12, 29, 30, 31 |
| Software Requirements Specification (SRS) | 9, 10, 11, 12, 13 |
| Software Design Document (SDD) | 14, 15, 16, 19, 20, 21, 22, 23, 27 |
| System Architecture Document | 2, 3, 4, 8, 28 |
| Database Design Document | 5, 6, 7, 8 |
| API Documentation | 18, 27 |
| AI/RAG Architecture Document | 14, 15, 16, 17, 25 |
| Developer Guide | 19, 20, 32 |
| Testing Guide | 24, 25 |
| Deployment Guide | 28, 32 |

### Writing Conventions (ASD-STE100-style)

This document follows the main principles of Simplified Technical English (ASD-STE100). It does not claim formal STE validation.

- Sentences are short. Procedure steps have one instruction each.
- Sentences use the active voice and the present tense.
- One word has one meaning. The glossary defines each project term.
- Requirement words have fixed meanings:

| Word | Meaning |
|---|---|
| **must** | The action is mandatory. |
| **must not** | The action is forbidden. |
| **should** | The action is recommended. |
| **can** | The action is possible or allowed. |

### Glossary

| Term | Definition |
|---|---|
| Socratic question | A question that helps the student find the answer without telling the answer. |
| Hint | A short help message that gives a small amount of information. |
| Hint level | A number from 0 to 3. A higher number gives more help. |
| Learner level | The estimated skill of the student: `beginner`, `intermediate` or `advanced`. |
| Difficulty | A number from 1 to 5 for the question in the current session. |
| Mastery | A number from 0 to 1 that shows how well the student knows a subject. |
| Misconception | A wrong belief or wrong reasoning rule in the student's answer. |
| Turn | One student message and the agent response to it. |
| Session | One tutoring conversation about one learning goal. |
| Agent state | The data that the agent keeps for one session (difficulty, hint level, streaks). |
| RAG | Retrieval-Augmented Generation. The system finds reference text and gives it to the LLM. |
| Chunk | A small part of a document that the system indexes in the vector store. |
| BFF | Backend for Frontend. The Next.js server code that calls the FastAPI backend for the browser. |
| JWT | JSON Web Token. A signed token that proves the identity of the user. |

---

## How This Document Is Organized

The document is split into short files. Section numbers (1 to 33) stay the same in all files, so cross-references such as "Section 17.6" still work. Each file has links to the previous and next file.

| File | Sections | Content |
|---|---|---|
| [01-overview-and-stack.md](01-overview-and-stack.md) | 1, 2 | Project Overview, Technology Stack |
| [02-architecture-and-ai-flow.md](02-architecture-and-ai-flow.md) | 3, 4 | Core System Architecture, AI Interaction Flow |
| [03-database-design.md](03-database-design.md) | 5, 6, 8 | Database Design, Database Relationships, Data Flow Between AI and Database |
| [04-database-schema.md](04-database-schema.md) | 7 | Database Schema Output |
| [05-requirements.md](05-requirements.md) | 9, 10, 11 | Functional Requirements, Non-Functional Requirements, User Roles |
| [06-user-stories-and-use-cases.md](06-user-stories-and-use-cases.md) | 12, 13 | User Stories, Use Cases |
| [07-socratic-agent.md](07-socratic-agent.md) | 14, 15, 16 | Socratic Agent Design, Adaptive Learning Logic, Prompt Architecture |
| [08-rag-faiss.md](08-rag-faiss.md) | 17 | RAG Architecture |
| [09-api.md](09-api.md) | 18 | API Design |
| [10-backend.md](10-backend.md) | 19 | FastAPI Backend Architecture |
| [11-frontend-and-ui.md](11-frontend-and-ui.md) | 20, 21 | Next.js Frontend Architecture, UI Design |
| [12-sequences-and-example-session.md](12-sequences-and-example-session.md) | 22, 23 | Sequence Diagrams, Learning Session Workflow |
| [13-testing-and-ai-evaluation.md](13-testing-and-ai-evaluation.md) | 24, 25 | Testing Strategy, AI Evaluation |
| [14-security-and-errors.md](14-security-and-errors.md) | 26, 27 | Security, Error Handling |
| [15-deployment.md](15-deployment.md) | 28 | Deployment Architecture |
| [16-roadmap-mvp-future.md](16-roadmap-mvp-future.md) | 29, 30, 31 | Development Roadmap, MVP Definition, Future Enhancements |
| [17-developer-guide.md](17-developer-guide.md) | 32 | Developer Guide |
| [18-consistency-check.md](18-consistency-check.md) | 33 | Final Output Requirements and Consistency Check |

## Reading Guide

| If you are a... | Read first |
|---|---|
| Product owner or reviewer | 01, 05, 06, 16 |
| Backend developer | 03, 04, 07, 08, 09, 10 |
| Frontend developer | 09, 11, 12 |
| AI / prompt engineer | 07, 08, 13 |
| QA engineer | 05, 13 |
| DevOps | 14, 15, 17 |
| New team member | 01, 02, then 17 (Developer Guide) |

## Key Decisions (Short Version)

- One **Socratic Agent** (no multi-agent design) with 10 internal capabilities.
- **Next.js + FastAPI + PostgreSQL + LangChain + LLM**.
- **RAG with FAISS**: FAISS stores only vectors. Chunk text and metadata stay in PostgreSQL. `document_chunks.vector_id` links the two. One index file for each subject.
- RAG is off in the MVP (`RAG_ENABLED=false`) and turns on in Release 1.1.
- The agent has no database access. The service layer saves each turn in one transaction.
