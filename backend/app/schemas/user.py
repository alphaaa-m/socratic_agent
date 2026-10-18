from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel
from app.schemas.validators import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    check_password_strength,
)


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
    current_password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        # Same rule as registration (FR-REG-04), so a password can never be
        # changed into something weaker than what registration would accept.
        return check_password_strength(value)


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
