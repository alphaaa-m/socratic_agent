import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import or_

from app.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument
    from app.models.learning_progress import LearningProgress
    from app.models.learning_session import LearningSession
    from app.models.user import User


class Subject(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (
        Index("ix_subjects_owner_id", "owner_id"),
        Index(
            "uq_subjects_default_name_ci",
            text("lower(name)"),
            unique=True,
            postgresql_where=text("owner_id IS NULL"),
        ),
        Index(
            "uq_subjects_owner_name_ci",
            "owner_id",
            text("lower(name)"),
            unique=True,
            postgresql_where=text("owner_id IS NOT NULL"),
        ),
    )

    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    owner: Mapped["User | None"] = relationship(back_populates="custom_subjects")
    sessions: Mapped[list["LearningSession"]] = relationship(back_populates="subject")
    progress: Mapped[list["LearningProgress"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", passive_deletes=True
    )
    documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="subject")

    @property
    def is_default(self) -> bool:
        return self.owner_id is None

    @classmethod
    def visible_to(cls, user_id: uuid.UUID):
        """Defaults plus the caller's own custom subjects. Phase 7 RAG stays per subject."""
        return or_(cls.owner_id.is_(None), cls.owner_id == user_id)
