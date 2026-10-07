"""Assessment endpoints (docs Sec 18.8) -- Phase 5."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas.assessment import AssessmentResponse

router = APIRouter(tags=["assessments"])


@router.get("/sessions/{session_id}/assessments", response_model=list[AssessmentResponse])
def list_assessments(session_id: UUID, user: CurrentUser, db: DB):
    from app.services.assessment_service import AssessmentService

    return AssessmentService(db).list_for_session(user, session_id)


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: UUID, user: CurrentUser, db: DB):
    from app.services.assessment_service import AssessmentService

    return AssessmentService(db).get(user, assessment_id)
