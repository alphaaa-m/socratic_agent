"""Auth endpoints (docs Sec 18.3) -- Phase 1."""

from fastapi import APIRouter

from app.api.deps import DB
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest, db: DB):
    from app.services.auth_service import AuthService

    return AuthService(db).register(body.name, body.email, body.password)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DB):
    from app.services.auth_service import AuthService

    return AuthService(db).login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: DB):
    from app.services.auth_service import AuthService

    return AuthService(db).refresh(body.refresh_token)
