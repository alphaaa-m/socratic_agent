"""Message endpoints (docs Sec 18.7) -- Phase 3."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import DB, CurrentUser
from app.core.rate_limit import limiter
from app.schemas.common import Page
from app.schemas.message import (
    HintResponse,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(prefix="/sessions/{session_id}", tags=["messages"])


def _tutoring(db: DB, request: Request):
    from app.core.config import get_settings
    from app.services.tutoring_service import TutoringService

    return TutoringService(db, request.app.state.agent, get_settings())


@router.get("/messages", response_model=Page[MessageResponse])
def list_messages(session_id: UUID, user: CurrentUser, db: DB, limit: int = 50, offset: int = 0):
    from app.services.tutoring_service import TutoringService

    return TutoringService(db).list_messages(user, session_id, limit, offset)


@router.post("/messages", response_model=SendMessageResponse, status_code=201)
@limiter.limit("20/minute")
def send_message(
    request: Request,
    session_id: UUID,
    body: SendMessageRequest,
    user: CurrentUser,
    db: DB,
):
    svc = _tutoring(db, request)
    return svc.handle_student_message(user, session_id, body.content)


@router.post("/hints", response_model=HintResponse, status_code=201)
@limiter.limit("20/minute")
def request_hint(request: Request, session_id: UUID, user: CurrentUser, db: DB):
    svc = _tutoring(db, request)
    return svc.handle_hint_request(user, session_id)
