# API Design

*Socratic Agent project document. [Index](README.md) | [← Previous](08-rag-faiss.md) | [Next →](10-backend.md)*

---

## 18. API Design

### 18.1 Conventions

| Item | Rule |
|---|---|
| Base URL | `/api/v1` |
| Format | JSON (`application/json`). File upload uses `multipart/form-data`. |
| Authentication | `Authorization: Bearer <access_token>` |
| IDs | UUID strings |
| Timestamps | ISO 8601, UTC (for example `2026-10-07T09:30:00Z`) |
| Pagination | Query `limit` (default 20, maximum 100) and `offset` (default 0). Response: `{ "items": [...], "total": 0, "limit": 20, "offset": 0 }` |
| Ownership | A student cannot see the resources of another user. The API returns `404` (not `403`) for them. |
| Error body | See 18.2 |

### 18.2 Error Format and Codes

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [{ "field": "email", "issue": "value is not a valid email address" }],
    "request_id": "7f3c2a9e5b1d4e8f"
  }
}
```

| HTTP | `code` | Meaning |
|---|---|---|
| 400 | `BAD_REQUEST` | Request cannot be processed. |
| 401 | `UNAUTHENTICATED`, `TOKEN_EXPIRED`, `TOKEN_INVALID` | Missing, wrong or expired credentials. |
| 403 | `FORBIDDEN` | The role is not allowed. |
| 404 | `NOT_FOUND` | The resource does not exist or is not visible to the user. |
| 409 | `CONFLICT`, `SESSION_NOT_ACTIVE`, `TURN_CONFLICT` | State conflict. |
| 413 | `FILE_TOO_LARGE` | Upload is larger than the limit. |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | File type is not allowed. |
| 422 | `VALIDATION_ERROR` | Input validation failed. |
| 429 | `RATE_LIMITED` | Too many requests. Header `Retry-After` is set. |
| 500 | `INTERNAL_ERROR` | Unexpected error. |
| 503 | `LLM_UNAVAILABLE` | The LLM call failed after retries. |
| 504 | `LLM_TIMEOUT` | The LLM call timed out after retries. |

### 18.3 Authentication APIs

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| POST | `/auth/register` | None | `RegisterRequest` | `UserResponse` | 201, 409, 422, 429 | Create a student account. |
| POST | `/auth/login` | None | `LoginRequest` | `TokenResponse` | 200, 401, 422, 429 | Authenticate and get tokens. |
| POST | `/auth/refresh` | Refresh token in body | `RefreshRequest` | `TokenResponse` | 200, 401 | Get a new access token. |

There is no logout endpoint. Tokens are stateless. The BFF removes the cookies on logout.

### 18.4 User APIs

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| GET | `/users/me` | Student, Admin | - | `UserResponse` | 200, 401 | Read own account. |
| PATCH | `/users/me` | Student, Admin | `UserUpdateRequest` (`name`) | `UserResponse` | 200, 401, 422 | Change own name. |
| POST | `/users/me/password` | Student, Admin | `PasswordChangeRequest` | - | 204, 400, 401, 422 | Change own password. |
| DELETE | `/users/me` | Student, Admin | - | - | 204, 401 | Delete own account and all own data. |
| GET | `/users/me/profile` | Student, Admin | - | `LearnerProfileResponse` | 200, 401 | Read learner profile. |
| PATCH | `/users/me/profile` | Student, Admin | `LearnerProfileUpdateRequest` (`learning_preferences`) | `LearnerProfileResponse` | 200, 401, 422 | Change learning preferences. |
| GET | `/users` | Admin | Query: `role`, `q`, `limit`, `offset` | `Page[UserResponse]` | 200, 401, 403 | List users. |
| PATCH | `/users/{user_id}` | Admin | `AdminUserUpdateRequest` (`role`, `is_active`) | `UserResponse` | 200, 401, 403, 404, 422 | Change role or disable an account. |

### 18.5 Subject APIs

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| GET | `/subjects` | Student, Admin | Query: `active_only` (default true) | `list[SubjectResponse]` | 200, 401 | List subjects. |
| GET | `/subjects/{subject_id}` | Student, Admin | - | `SubjectResponse` | 200, 401, 404 | Read one subject. |
| POST | `/subjects` | Admin | `SubjectCreateRequest` | `SubjectResponse` | 201, 401, 403, 409, 422 | Create a subject. |
| PATCH | `/subjects/{subject_id}` | Admin | `SubjectUpdateRequest` | `SubjectResponse` | 200, 401, 403, 404, 409, 422 | Change or retire a subject. |
| DELETE | `/subjects/{subject_id}` | Admin | - | - | 204, 401, 403, 404, 409 | Delete a subject that has no sessions and no documents. |

### 18.6 Session APIs

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| POST | `/sessions` | Student, Admin | `SessionCreateRequest` (`subject_id`) | `SessionResponse` | 201, 401, 404, 422 | Start a session. |
| GET | `/sessions` | Student, Admin | Query: `subject_id`, `status`, `limit`, `offset` | `Page[SessionResponse]` | 200, 401 | List own sessions (newest first). |
| GET | `/sessions/{session_id}` | Owner | - | `SessionDetailResponse` | 200, 401, 404 | Read one session with state and summary. |
| POST | `/sessions/{session_id}/end` | Owner | - | `SessionDetailResponse` | 200, 401, 404, 409 | End the session and create the summary. |
| GET | `/sessions/{session_id}/summary` | Owner | - | `SessionSummaryResponse` | 200, 401, 404 | Read the saved summary. |

### 18.7 Message APIs

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| GET | `/sessions/{session_id}/messages` | Owner | Query: `limit`, `offset` | `Page[MessageResponse]` | 200, 401, 404 | Read the conversation in time order. |
| POST | `/sessions/{session_id}/messages` | Owner | `SendMessageRequest` | `SendMessageResponse` | 201, 401, 404, 409, 422, 429, 503, 504 | Send a question or an answer. Get the agent reply. |
| POST | `/sessions/{session_id}/hints` | Owner | - | `HintResponse` | 201, 401, 404, 409, 429, 503, 504 | Ask for a hint with the hint button. |

### 18.8 Assessment APIs

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| GET | `/sessions/{session_id}/assessments` | Owner | - | `list[AssessmentResponse]` | 200, 401, 404 | Read all assessments of a session. |
| GET | `/assessments/{assessment_id}` | Owner | - | `AssessmentResponse` | 200, 401, 404 | Read one assessment. |

### 18.9 Progress APIs

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| GET | `/progress` | Student, Admin | - | `ProgressOverviewResponse` | 200, 401 | Level, strengths, weaknesses, mastery for all subjects. |
| GET | `/progress/{subject_id}` | Student, Admin | - | `SubjectProgressResponse` | 200, 401, 404 | Mastery and score trend for one subject. |

### 18.10 Document APIs

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| GET | `/documents` | Admin | Query: `subject_id`, `status`, `limit`, `offset` | `Page[DocumentResponse]` | 200, 401, 403 | List documents. |
| POST | `/documents` | Admin | `multipart/form-data`: `file`, `subject_id`, `title`, `description?`, `source?` | `DocumentResponse` | 202, 401, 403, 404, 409, 413, 415, 422 | Upload a document. Processing runs in the background. |
| GET | `/documents/{document_id}` | Admin | - | `DocumentResponse` | 200, 401, 403, 404 | Read status and metadata. |
| DELETE | `/documents/{document_id}` | Admin | - | - | 204, 401, 403, 404, 502 | Delete vectors and rows. |
| POST | `/documents/{document_id}/reindex` | Admin | - | `DocumentResponse` | 202, 401, 403, 404 | Rebuild chunks and vectors. |
| GET | `/documents/{document_id}/chunks` | Admin | Query: `limit`, `offset` | `Page[ChunkResponse]` | 200, 401, 403, 404 | Read chunks. |
| POST | `/documents/search` | Admin | `RetrievalTestRequest` | `list[RetrievedChunkResponse]` | 200, 401, 403, 422 | Test retrieval. |

### 18.11 Health API

| Method | URL | Auth | Request body | Response body | Status codes | Purpose |
|---|---|---|---|---|---|---|
| GET | `/health` | None | - | `{ "status": "ok", "database": "ok", "vector_store": "ok" }` | 200, 503 | Monitoring and deployment check. |

The vector store field is `"disabled"` when `RAG_ENABLED=false`.

### 18.12 Request and Response Schemas

```python
# app/schemas/*.py  (Pydantic v2) - main schemas
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int                                   # seconds


class UserResponse(ORMModel):
    id: UUID
    name: str
    email: EmailStr
    role: Literal["student", "admin"]
    is_active: bool
    created_at: datetime


class SessionCreateRequest(BaseModel):
    subject_id: UUID


class SessionResponse(ORMModel):
    id: UUID
    subject_id: UUID
    title: str
    status: Literal["active", "completed", "abandoned"]
    started_at: datetime
    ended_at: datetime | None


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageResponse(ORMModel):
    id: UUID
    session_id: UUID
    sender: Literal["student", "agent", "system"]
    message_type: Literal["question", "response", "guidance", "hint", "summary", "system"]
    content: str
    created_at: datetime


class AssessmentResponse(ORMModel):
    id: UUID
    session_id: UUID
    message_id: UUID
    correctness_score: float
    reasoning_score: float
    confidence_score: float
    difficulty_level: int
    misconception: str | None
    feedback: str | None
    resolves_goal: bool
    created_at: datetime


class SessionStateResponse(BaseModel):
    status: Literal["active", "completed", "abandoned"]
    difficulty: int
    hint_level: int
    resolved: bool
    learner_level: Literal["beginner", "intermediate", "advanced"]
    rag_status: Literal["off", "ok", "empty", "error"]


class SendMessageResponse(BaseModel):
    student_message: MessageResponse
    agent_message: MessageResponse
    assessment: AssessmentResponse | None            # null for the first message
    session_state: SessionStateResponse


class HintResponse(BaseModel):
    agent_message: MessageResponse
    session_state: SessionStateResponse
```

### 18.13 Example Requests and Responses

**Register - `POST /api/v1/auth/register`**

```json
// Request
{ "name": "Amina Khan", "email": "Amina@Example.com", "password": "Secure123pass" }

// Response 201
{
  "id": "5b0b4e9a-3d57-4f0a-9d63-0c7d3a1f2b11",
  "name": "Amina Khan",
  "email": "amina@example.com",
  "role": "student",
  "is_active": true,
  "created_at": "2026-10-07T09:30:00Z"
}
```

**Login - `POST /api/v1/auth/login`**

```json
// Request
{ "email": "amina@example.com", "password": "Secure123pass" }

// Response 200
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Start session - `POST /api/v1/sessions`**

```json
// Request
{ "subject_id": "0e7a1b52-8c0c-4d5e-8f1e-5a2b3c4d5e6f" }

// Response 201
{
  "id": "c1d2e3f4-0a1b-4c2d-8e3f-a4b5c6d7e8f9",
  "subject_id": "0e7a1b52-8c0c-4d5e-8f1e-5a2b3c4d5e6f",
  "title": "New session",
  "status": "active",
  "started_at": "2026-10-07T09:40:00Z",
  "ended_at": null
}
```

**Send message - `POST /api/v1/sessions/{session_id}/messages`**

```json
// Request
{ "content": "0.333 I guess? I do not see how this helps. Can I have a hint?" }

// Response 201
{
  "student_message": {
    "id": "a1...", "session_id": "c1d2...", "sender": "student",
    "message_type": "response",
    "content": "0.333 I guess? I do not see how this helps. Can I have a hint?",
    "created_at": "2026-10-07T09:42:10Z"
  },
  "agent_message": {
    "id": "b2...", "session_id": "c1d2...", "sender": "agent",
    "message_type": "hint",
    "content": "Here is a nudge. Some fractions end as decimals in base 10, and some do not. Try 1/2, 1/4, 1/5 and 1/3. Which ones end? What do their denominators have in common?",
    "created_at": "2026-10-07T09:42:14Z"
  },
  "assessment": {
    "id": "d3...", "session_id": "c1d2...", "message_id": "a1...",
    "correctness_score": 0.4, "reasoning_score": 0.3, "confidence_score": 0.4,
    "difficulty_level": 2,
    "misconception": "treats a rounded decimal as an exact value",
    "feedback": "Good start. Look again at the word 'exact'.",
    "resolves_goal": false,
    "created_at": "2026-10-07T09:42:14Z"
  },
  "session_state": {
    "status": "active", "difficulty": 2, "hint_level": 1,
    "resolved": false, "learner_level": "beginner", "rag_status": "off"
  }
}
```

**End session - `POST /api/v1/sessions/{session_id}/end`**

```json
// Response 200
{
  "id": "c1d2...",
  "subject_id": "0e7a...",
  "title": "Why does 0.1 + 0.2 == 0.3 return False?",
  "status": "completed",
  "started_at": "2026-10-07T09:40:00Z",
  "ended_at": "2026-10-07T09:55:00Z",
  "summary": {
    "outcome": "resolved",
    "overview": "You explained why 0.1 + 0.2 is not exactly 0.3 in Python. You found the rule for which fractions end in a number base.",
    "key_concepts": ["binary fractions", "finite and repeating expansions", "floating-point rounding"],
    "strengths": ["You found a general rule from examples."],
    "misconceptions_addressed": ["treats a rounded decimal as an exact value"],
    "areas_to_review": ["comparing floats with a tolerance"],
    "next_steps": ["Try math.isclose() on three examples."],
    "generated_by": "llm"
  }
}
```

**Upload document - `POST /api/v1/documents`** (`multipart/form-data`)

```text
file=@python_numbers.pdf  subject_id=0e7a1b52-...  title="Python Numbers"  source="Course notes, week 2"

Response 202
{ "id": "f0...", "subject_id": "0e7a...", "title": "Python Numbers", "file_name": "python_numbers.pdf",
  "status": "pending", "error_message": null, "created_at": "2026-10-07T10:00:00Z" }
```

**Retrieval test - `POST /api/v1/documents/search`**

```json
// Request
{ "subject_id": "0e7a1b52-...", "query": "why 0.1 + 0.2 is not 0.3", "top_k": 4 }

// Response 200
[
  { "chunk_id": "9a...", "document_id": "f0...", "title": "Python Numbers", "score": 0.71,
    "content": "Floating-point numbers use binary fractions. Most decimal fractions do not have an exact binary form..." }
]
```

### 18.14 Routers and Dependencies

```python
# app/api/deps.py
import uuid
from typing import Annotated
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthenticatedError
from app.database.session import get_db
from app.models import User
from app.services.tutoring_service import TutoringService

bearer = HTTPBearer(auto_error=False)
DB = Annotated[Session, Depends(get_db)]


def get_current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], db: DB) -> User:
    if creds is None:
        raise UnauthenticatedError()
    payload = decode_token(creds.credentials, expected_type="access")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthenticatedError()
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise ForbiddenError()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]


def get_tutoring_service(request: Request, db: DB) -> TutoringService:
    # The agent is built once at startup (lifespan) and shared. It keeps no per-request state.
    return TutoringService(db, request.app.state.agent, get_settings())
```

```python
# app/api/v1/messages.py
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from app.api.deps import DB, CurrentUser, get_tutoring_service
from app.core.rate_limit import limiter
from app.schemas.message import HintResponse, MessageResponse, Page, SendMessageRequest, SendMessageResponse
from app.services.tutoring_service import TutoringService

router = APIRouter(prefix="/sessions/{session_id}", tags=["messages"])


@router.get("/messages", response_model=Page[MessageResponse])
def list_messages(session_id: UUID, user: CurrentUser, db: DB, limit: int = 50, offset: int = 0):
    return TutoringService(db).list_messages(user, session_id, limit, offset)


@router.post("/messages", response_model=SendMessageResponse, status_code=201)
@limiter.limit("20/minute")
def send_message(request: Request, session_id: UUID, body: SendMessageRequest,
                 user: CurrentUser, svc: TutoringService = Depends(get_tutoring_service)):
    return svc.handle_student_message(user, session_id, body.content)


@router.post("/hints", response_model=HintResponse, status_code=201)
@limiter.limit("20/minute")
def request_hint(request: Request, session_id: UUID, user: CurrentUser,
                 svc: TutoringService = Depends(get_tutoring_service)):
    return svc.handle_hint_request(user, session_id)
```

---

*[Index](README.md) | [← Previous](08-rag-faiss.md) | [Next →](10-backend.md)*
