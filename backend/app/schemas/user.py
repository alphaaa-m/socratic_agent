from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class UserResponse(ORMModel):
    id: UUID
    name: str
    email: str
    role: Literal["student", "admin"]
    is_active: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AdminUserUpdateRequest(BaseModel):
    role: Literal["student", "admin"] | None = None
    is_active: bool | None = None


class LearnerProfileResponse(ORMModel):
    user_id: UUID
    current_level: Literal["beginner", "intermediate", "advanced"]
    level_score: float
    assessment_count: int
    learning_preferences: dict
    strengths: list
    weaknesses: list
    total_sessions: int


class LearnerProfileUpdateRequest(BaseModel):
    learning_preferences: dict
