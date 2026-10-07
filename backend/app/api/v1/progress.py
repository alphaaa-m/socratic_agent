"""Progress endpoints (docs Sec 18.9) -- Phase 6."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas.progress import ProgressOverviewResponse, SubjectProgressResponse

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressOverviewResponse)
def get_overview(user: CurrentUser, db: DB):
    from app.services.progress_service import ProgressService

    return ProgressService(db).overview(user)


@router.get("/{subject_id}", response_model=SubjectProgressResponse)
def get_subject_progress(subject_id: UUID, user: CurrentUser, db: DB):
    from app.services.progress_service import ProgressService

    return ProgressService(db).for_subject(user, subject_id)
