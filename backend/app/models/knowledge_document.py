import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk
    from app.models.subject import Subject


class KnowledgeDocument(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        UniqueConstraint("subject_id", "content_hash"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'indexed', 'failed')", name="status_valid"
        ),
        Index("ix_knowledge_documents_subject_id_status", "subject_id", "status"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String(255))
    source: Mapped[str | None] = mapped_column(String(500))
    content_hash: Mapped[str] = mapped_column(CHAR(64))
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    subject: Mapped["Subject"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True,
        order_by="DocumentChunk.chunk_index",
    )
