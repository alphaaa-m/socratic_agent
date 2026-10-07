"""Session endpoints (docs Sec 18.6) -- Phase 2 (CRUD), Phase 6 (end/summary)."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas.common import Page
from app.schemas.session import (
    SessionCreateRequest,
    SessionDetailResponse,
    SessionResponse,
    SessionSummaryResponse,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(body: SessionCreateRequest, user: CurrentUser, db: DB):
    from app.services.session_service import SessionService

    return SessionService(db).create(user, body.subject_id)


@router.get("", response_model=Page[SessionResponse])
def list_sessions(
    user: CurrentUser,
    db: DB,
    subject_id: UUID | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    from app.services.session_service import SessionService

    return SessionService(db).list(user, subject_id, status, limit, offset)


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: UUID, user: CurrentUser, db: DB):
    from app.services.session_service import SessionService

    return SessionService(db).get(user, session_id)


@router.post("/{session_id}/end", response_model=SessionDetailResponse)
def end_session(session_id: UUID, user: CurrentUser, db: DB):
    from app.services.session_service import SessionService

    return SessionService(db).end_session(user, session_id)


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse)
def get_summary(session_id: UUID, user: CurrentUser, db: DB):
    from app.services.session_service import SessionService

    return SessionService(db).get_summary(user, session_id)
