"""User/account service -- Phase 1 (account), Phase 2 (admin) (FR-ACC-*)."""

from sqlalchemy.orm import Session


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user):
        raise NotImplementedError("TODO(phase-1): return own account (FR-ACC-01)")

    def update_me(self, user, name: str):
        raise NotImplementedError("TODO(phase-1): change own name (FR-ACC-01)")

    def change_password(self, user, current_password: str, new_password: str):
        raise NotImplementedError("TODO(phase-1): change own password (FR-ACC-01)")

    def delete_me(self, user):
        raise NotImplementedError("TODO(phase-6): delete own account + cascade data (FR-ACC-02)")

    def update_profile(self, user, preferences: dict):
        raise NotImplementedError("TODO(phase-1): update learning_preferences")

    def list_users(self, role=None, q=None, limit: int = 20, offset: int = 0):
        raise NotImplementedError("TODO(phase-2): admin list users (FR-ACC-03)")

    def admin_update(self, user_id, role=None, is_active=None):
        raise NotImplementedError("TODO(phase-2): admin change role/disable (FR-ACC-03)")
