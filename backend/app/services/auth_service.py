"""Auth service -- Phase 1 (FR-REG-*, FR-LOG-*, FR-JWT-*)."""

import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.jwt import ACCESS, REFRESH, create_token, decode_token
from app.auth.passwords import hash_password, verify_password
from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthenticatedError
from app.models import LearnerProfile, User
from app.schemas.auth import TokenResponse

# One message for "unknown email" and "wrong password" (FR-LOG-02).
INVALID_CREDENTIALS = "Email or password is incorrect."
EMAIL_TAKEN = "An account with this email already exists."
ACCOUNT_DISABLED = "This account has been disabled."
# Keep the unknown-email path close in cost to a real password check so login
# timing does not reveal whether an address has an account.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-account-password")


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, name: str, email: str, password: str) -> User:
        """FR-REG-01..06: create student + learner_profiles row in one transaction."""
        normalized_email = email.strip().lower()

        existing = self.db.scalar(select(User.id).where(User.email == normalized_email))
        if existing is not None:
            raise ConflictError(EMAIL_TAKEN)

        user = User(
            name=name.strip(),
            email=normalized_email,
            password_hash=hash_password(password),
            role="student",
        )
        self.db.add(user)
        try:
            self.db.flush()
            # FR-REG-05: the profile belongs to the same transaction.
            self.db.add(LearnerProfile(user_id=user.id))
            self.db.commit()
        except IntegrityError:
            # Two registrations for the same email can race; the UNIQUE index wins.
            self.db.rollback()
            raise ConflictError(EMAIL_TAKEN) from None

        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> TokenResponse:
        """FR-LOG-01..04: authenticate, check is_active, issue token pair."""
        user = self.db.scalar(select(User).where(User.email == email.strip().lower()))

        if user is None:
            verify_password(password, _DUMMY_PASSWORD_HASH)
            raise UnauthenticatedError(INVALID_CREDENTIALS)
        if not verify_password(password, user.password_hash):
            raise UnauthenticatedError(INVALID_CREDENTIALS)

        # Checked after the password so a stranger cannot probe for accounts by
        # seeing a different answer for a disabled one.
        if not user.is_active:
            raise UnauthenticatedError(ACCOUNT_DISABLED)

        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> TokenResponse:
        """FR-JWT-04: accept only refresh tokens, return new token pair."""
        payload = decode_token(refresh_token, expected_type=REFRESH)

        user = self.db.get(User, uuid.UUID(str(payload["sub"])))
        if user is None or not user.is_active:
            raise UnauthenticatedError()

        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        settings = get_settings()
        access_lifetime = timedelta(minutes=settings.access_token_minutes)
        refresh_lifetime = timedelta(days=settings.refresh_token_days)
        return TokenResponse(
            access_token=create_token(user.id, user.role, ACCESS, access_lifetime),
            refresh_token=create_token(user.id, user.role, REFRESH, refresh_lifetime),
            expires_in=int(access_lifetime.total_seconds()),
        )
