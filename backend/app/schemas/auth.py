from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.validators import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    check_password_strength,
)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        return check_password_strength(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
