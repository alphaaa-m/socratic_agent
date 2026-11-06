from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", mode="wrap", when_used="json")
    def _uuid_as_str(self, value, handler):
        if isinstance(value, UUID):
            return str(value)
        return handler(value)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
