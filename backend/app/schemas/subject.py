from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.schemas.common import ORMModel


class SubjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class SubjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    is_active: bool | None = None


class SubjectResponse(ORMModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    owner_id: UUID | None = None
    created_at: datetime

    @computed_field
    @property
    def is_default(self) -> bool:
        return self.owner_id is None
