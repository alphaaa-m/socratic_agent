"""User/account service -- Phase 1 (account), Phase 2 (admin) (FR-ACC-*)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password, verify_password
from app.core.exceptions import BadRequestError, NotFoundError
from app.models import LearnerProfile, User


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user: User) -> User:
        """Return the caller's own account (FR-ACC-01)."""
        return user

    def update_me(self, user: User, name: str) -> User:
        """FR-ACC-01: change own name."""
        user.name = name.strip()
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        """FR-ACC-01: change own password after proving the current one."""
        if not verify_password(current_password, user.password_hash):
            raise BadRequestError("The current password is not correct.")
        user.password_hash = hash_password(new_password)
        self.db.commit()

    def delete_me(self, user: User) -> None:
        """FR-ACC-02: delete own account; the database cascades all personal data.

        ``users`` is the head of the cascade chain (learner_profiles,
        learning_sessions, learning_progress, messages, learner_assessments), so
        removing this one row removes every trace of the learner. Uploaded
        knowledge documents survive with ``uploaded_by`` set to NULL.
        """
        self.db.delete(user)
        self.db.commit()

    def get_learner_profile(self, user: User) -> LearnerProfile:
        """Read the caller's own learner profile.

        Registration always creates the row (FR-REG-05), so a missing profile
        means the data is inconsistent -- report it instead of inventing one.
        """
        profile = self.db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user.id))
        if profile is None:
            raise NotFoundError("Learner profile not found.")
        return profile

    def update_profile(self, user: User, preferences: dict) -> LearnerProfile:
        """Replace ``learning_preferences`` (nothing else is writable here)."""
        profile = self.get_learner_profile(user)
        profile.learning_preferences = preferences or {}
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_users(self, role=None, q=None, limit: int = 20, offset: int = 0):
        raise NotImplementedError("TODO(phase-2): admin list users (FR-ACC-03)")

    def admin_update(self, user_id, role=None, is_active=None):
        raise NotImplementedError("TODO(phase-2): admin change role/disable (FR-ACC-03)")
