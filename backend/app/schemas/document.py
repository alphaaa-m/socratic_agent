from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DocumentResponse(ORMModel):
    id: UUID
    subject_id: UUID
    title: str
    description: str | None = None
    file_name: str
    source: str | None = None
    status: Literal["pending", "processing", "indexed", "failed"]
    error_message: str | None = None
    created_at: datetime


class ChunkResponse(ORMModel):
    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    created_at: datetime


class RetrievalTestRequest(BaseModel):
    subject_id: UUID
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=4, ge=1, le=20)


class RetrievedChunkResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    title: str
    score: float
    content: str
