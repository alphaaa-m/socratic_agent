from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.assessment import AssessmentResponse
from app.schemas.common import ORMModel
from app.schemas.session import SessionStateResponse


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageResponse(ORMModel):
    id: UUID
    session_id: UUID
    sender: Literal["student", "agent", "system"]
    message_type: Literal["question", "response", "guidance", "hint", "summary", "system"]
    content: str
    created_at: datetime


class SendMessageResponse(BaseModel):
    student_message: MessageResponse
    agent_message: MessageResponse
    assessment: AssessmentResponse | None = None
    session_state: SessionStateResponse


class HintResponse(BaseModel):
    agent_message: MessageResponse
    session_state: SessionStateResponse
