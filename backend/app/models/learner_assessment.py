import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.learning_session import LearningSession
    from app.models.message import Message


def _score() -> Mapped[float]:
    return mapped_column(Numeric(4, 3, asdecimal=False))


class LearnerAssessment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "learner_assessments"
    __table_args__ = (
        CheckConstraint("correctness_score BETWEEN 0 AND 1", name="correctness_range"),
        CheckConstraint("reasoning_score BETWEEN 0 AND 1", name="reasoning_range"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("difficulty_level BETWEEN 1 AND 5", name="difficulty_range"),
        Index("ix_learner_assessments_session_id_created_at", "session_id", "created_at"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), unique=True
    )
    correctness_score: Mapped[float] = _score()
    reasoning_score: Mapped[float] = _score()
    confidence_score: Mapped[float] = _score()
    difficulty_level: Mapped[int] = mapped_column(SmallInteger)
    misconception: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)
    resolves_goal: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    session: Mapped["LearningSession"] = relationship(back_populates="assessments")
    message: Mapped["Message"] = relationship(back_populates="assessment")
