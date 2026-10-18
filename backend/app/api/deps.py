"""Auth dependencies (docs Sec 18.14). get_db is complete; auth is Phase 1."""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import ACCESS, decode_token
from app.core.exceptions import ForbiddenError, UnauthenticatedError
from app.database.session import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)
DB = Annotated[Session, Depends(get_db)]


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: DB,
) -> User:
    """Decode the access token and load the user from the database.

    The role stored in the token is deliberately ignored: the database row is the
    source of truth (FR-JWT-05), so a disabled account loses access immediately.
    """
    if creds is None or not creds.credentials:
        raise UnauthenticatedError()

    payload = decode_token(creds.credentials, expected_type=ACCESS)
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError):
        raise UnauthenticatedError("Your session token is not valid.", code="TOKEN_INVALID") from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthenticatedError()
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Allow only administrators (docs Sec 18.14)."""
    if user.role != "admin":
        raise ForbiddenError("Administrator access is required.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
