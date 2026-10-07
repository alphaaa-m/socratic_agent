from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class SubjectProgressResponse(BaseModel):
    subject_id: UUID
    subject_name: str
    mastery_score: float
    topics_attempted: int
    topics_mastered: int
    last_activity_at: datetime | None = None
    recent_scores: list[float] = []


class ProgressOverviewResponse(BaseModel):
    current_level: Literal["beginner", "intermediate", "advanced"]
    level_score: float
    strengths: list
    weaknesses: list
    subjects: list[SubjectProgressResponse]


class ProgressResponse(ORMModel):
    user_id: UUID
    subject_id: UUID
    mastery_score: float
    topics_attempted: int
    topics_mastered: int
    last_activity_at: datetime | None = None
