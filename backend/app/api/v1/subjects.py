"""Subject endpoints (docs Sec 18.5) -- Phase 2."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DB, AdminUser, CurrentUser
from app.schemas.subject import (
    SubjectCreateRequest,
    SubjectResponse,
    SubjectUpdateRequest,
)

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectResponse])
def list_subjects(user: CurrentUser, db: DB, active_only: bool = True):
    from app.services.subject_service import SubjectService

    return SubjectService(db).list(active_only)


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: UUID, user: CurrentUser, db: DB):
    from app.services.subject_service import SubjectService

    return SubjectService(db).get(user, subject_id)


@router.post("", response_model=SubjectResponse, status_code=201)
def create_subject(body: SubjectCreateRequest, user: AdminUser, db: DB):
    from app.services.subject_service import SubjectService

    return SubjectService(db).create(user, body.name, body.description)


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(subject_id: UUID, body: SubjectUpdateRequest, user: AdminUser, db: DB):
    from app.services.subject_service import SubjectService

    return SubjectService(db).update(user, subject_id, **body.model_dump(exclude_unset=True))


@router.delete("/{subject_id}", status_code=204)
def delete_subject(subject_id: UUID, user: AdminUser, db: DB):
    from app.services.subject_service import SubjectService

    SubjectService(db).delete(user, subject_id)
