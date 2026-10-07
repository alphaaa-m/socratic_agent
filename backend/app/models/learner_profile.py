import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class LearnerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learner_profiles"
    __table_args__ = (
        CheckConstraint(
            "current_level IN ('beginner', 'intermediate', 'advanced')", name="level_valid"
        ),
        CheckConstraint("level_score BETWEEN 0 AND 1", name="level_score_range"),
        CheckConstraint("assessment_count >= 0 AND total_sessions >= 0", name="counts_nonnegative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    current_level: Mapped[str] = mapped_column(default="beginner", server_default="beginner")
    level_score: Mapped[float] = mapped_column(
        Numeric(4, 3, asdecimal=False), default=0.3, server_default=text("0.300")
    )
    assessment_count: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    learning_preferences: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    strengths: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    weaknesses: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    total_sessions: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    user: Mapped["User"] = relationship(back_populates="profile")
