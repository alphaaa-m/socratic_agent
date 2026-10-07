from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel

SessionStatus = Literal["active", "completed", "abandoned"]


class SessionCreateRequest(BaseModel):
    subject_id: UUID


class SessionResponse(ORMModel):
    id: UUID
    subject_id: UUID
    title: str
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None


class SessionDetailResponse(SessionResponse):
    agent_state: dict
    summary: dict | None = None


class SessionStateResponse(BaseModel):
    status: SessionStatus
    difficulty: int
    hint_level: int
    resolved: bool
    learner_level: Literal["beginner", "intermediate", "advanced"]
    rag_status: Literal["off", "ok", "empty", "error"]


class SessionSummaryResponse(BaseModel):
    session_id: UUID
    status: SessionStatus
    summary: dict | None = None
