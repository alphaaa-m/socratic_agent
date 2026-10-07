import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.subject import Subject
    from app.models.user import User


class LearningProgress(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "subject_id"),
        CheckConstraint("mastery_score BETWEEN 0 AND 1", name="mastery_range"),
        CheckConstraint(
            "topics_attempted >= 0 AND topics_mastered >= 0 AND topics_mastered <= topics_attempted",
            name="topics_valid",
        ),
        Index("ix_learning_progress_subject_id", "subject_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    mastery_score: Mapped[float] = mapped_column(
        Numeric(4, 3, asdecimal=False), default=0.0, server_default=text("0")
    )
    topics_attempted: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    topics_mastered: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    last_activity_at: Mapped[datetime | None] = mapped_column()

    user: Mapped["User"] = relationship(back_populates="progress")
    subject: Mapped["Subject"] = relationship(back_populates="progress")
