"""User endpoints (docs Sec 18.4) -- Phase 1 (account), Phase 2 (admin)."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import DB, AdminUser, CurrentUser
from app.models.enums import UserRole
from app.schemas.common import Page
from app.schemas.user import (
    AdminUserUpdateRequest,
    LearnerProfileResponse,
    LearnerProfileUpdateRequest,
    PasswordChangeRequest,
    UserResponse,
    UserUpdateRequest,
)

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=UserResponse)
def get_me(user: CurrentUser, db: DB):
    from app.services.user_service import UserService

    return UserService(db).get_profile(user)


@router.patch("/users/me", response_model=UserResponse)
def update_me(body: UserUpdateRequest, user: CurrentUser, db: DB):
    from app.services.user_service import UserService

    return UserService(db).update_me(user, body.name)


@router.post("/users/me/password", status_code=204)
def change_password(body: PasswordChangeRequest, user: CurrentUser, db: DB):
    from app.services.user_service import UserService

    UserService(db).change_password(user, body.current_password, body.new_password)


@router.delete("/users/me", status_code=204)
def delete_me(user: CurrentUser, db: DB):
    from app.services.user_service import UserService

    UserService(db).delete_me(user)


@router.get("/users/me/profile", response_model=LearnerProfileResponse)
def get_my_profile(user: CurrentUser, db: DB):
    from app.services.user_service import UserService

    return UserService(db).get_learner_profile(user)


@router.patch("/users/me/profile", response_model=LearnerProfileResponse)
def update_my_profile(body: LearnerProfileUpdateRequest, user: CurrentUser, db: DB):
    from app.services.user_service import UserService

    return UserService(db).update_profile(user, body.learning_preferences)


@router.get("/users", response_model=Page[UserResponse])
def list_users(
    user: AdminUser,
    db: DB,
    role: UserRole | None = None,
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    from app.services.user_service import UserService

    return UserService(db).list_users(role=role, q=q, limit=limit, offset=offset)


@router.patch("/users/{user_id}", response_model=UserResponse)
def admin_update_user(user_id: UUID, body: AdminUserUpdateRequest, user: AdminUser, db: DB):
    from app.services.user_service import UserService

    return UserService(db).admin_update(user, user_id, body.role, body.is_active)
