from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.learner_profile import LearnerProfile
    from app.models.learning_progress import LearningProgress
    from app.models.learning_session import LearningSession


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin')", name="role_valid"),
        CheckConstraint("email = lower(email)", name="email_lowercase"),
    )

    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student", server_default="student")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    profile: Mapped["LearnerProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    sessions: Mapped[list["LearningSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    progress: Mapped[list["LearningProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
