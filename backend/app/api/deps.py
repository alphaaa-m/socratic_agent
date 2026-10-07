"""Auth dependencies (docs Sec 18.14). get_db is complete; auth is Phase 1."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.session import get_db

bearer = HTTPBearer(auto_error=False)
DB = Annotated[Session, Depends(get_db)]


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: DB,
):
    raise NotImplementedError("TODO(phase-1): decode access JWT, load active user from DB")


def require_admin(user: Annotated[object, Depends(get_current_user)]):
    raise NotImplementedError("TODO(phase-1): require role == admin (403 otherwise)")


CurrentUser = Annotated[object, Depends(get_current_user)]
AdminUser = Annotated[object, Depends(require_admin)]
