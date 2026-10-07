import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.learner_assessment import LearnerAssessment
    from app.models.learning_session import LearningSession


class Message(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("sender IN ('student', 'agent', 'system')", name="sender_valid"),
        CheckConstraint(
            "message_type IN ('question', 'response', 'guidance', 'hint', 'summary', 'system')",
            name="type_valid",
        ),
        CheckConstraint("char_length(content) > 0", name="content_not_empty"),
        CheckConstraint(
            "(sender = 'student' AND message_type IN ('question', 'response')) OR "
            "(sender = 'agent' AND message_type IN ('guidance', 'hint', 'summary')) OR "
            "(sender = 'system' AND message_type = 'system')",
            name="sender_type_consistent",
        ),
        Index("ix_messages_session_id_created_at", "session_id", "created_at"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    sender: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(String(20))
    retrieved_chunk_ids: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )

    session: Mapped["LearningSession"] = relationship(back_populates="messages")
    assessment: Mapped["LearnerAssessment | None"] = relationship(
        back_populates="message", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
