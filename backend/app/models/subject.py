from typing import TYPE_CHECKING

from sqlalchemy import String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument
    from app.models.learning_progress import LearningProgress
    from app.models.learning_session import LearningSession


class Subject(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    sessions: Mapped[list["LearningSession"]] = relationship(back_populates="subject")
    progress: Mapped[list["LearningProgress"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", passive_deletes=True
    )
    documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="subject")
