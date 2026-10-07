from datetime import datetime
from uuid import UUID

from app.schemas.common import ORMModel


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
