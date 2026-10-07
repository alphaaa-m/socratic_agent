import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.learner_assessment import LearnerAssessment
    from app.models.message import Message
    from app.models.subject import Subject
    from app.models.user import User


class LearningSession(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "learning_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'completed', 'abandoned')", name="status_valid"),
        CheckConstraint("(status = 'active') = (ended_at IS NULL)", name="ended_matches_status"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ended_after_start"),
        Index("ix_learning_sessions_user_id_started_at", "user_id", text("started_at DESC")),
        Index("ix_learning_sessions_user_id_status", "user_id", "status"),
        Index("ix_learning_sessions_subject_id", "subject_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(255), default="New session", server_default="New session")
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    agent_state: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    summary: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    ended_at: Mapped[datetime | None] = mapped_column()

    user: Mapped["User"] = relationship(back_populates="sessions")
    subject: Mapped["Subject"] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Message.created_at",
    )
    assessments: Mapped[list["LearnerAssessment"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True,
        order_by="LearnerAssessment.created_at",
    )
