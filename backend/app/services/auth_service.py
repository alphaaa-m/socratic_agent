"""Auth service -- Phase 1 (FR-REG-*, FR-LOG-*, FR-JWT-*)."""

from sqlalchemy.orm import Session


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, name: str, email: str, password: str):
        """FR-REG-01..06: create student + learner_profiles row in one transaction."""
        raise NotImplementedError("TODO(phase-1): register student (lowercase email, Argon2, profile row)")

    def login(self, email: str, password: str):
        """FR-LOG-01..04: authenticate, check is_active, issue token pair."""
        raise NotImplementedError("TODO(phase-1): login (same error for unknown/wrong, rate limited)")

    def refresh(self, refresh_token: str):
        """FR-JWT-04: accept only refresh tokens, return new token pair."""
        raise NotImplementedError("TODO(phase-1): refresh access token from refresh token")
