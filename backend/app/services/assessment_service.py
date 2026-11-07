"""Assessment service -- Phase 5 (FR-EVA-*, FR-HIS-03)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.ids import require_uuid
from app.models import LearnerAssessment, LearningSession


class AssessmentService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_session(self, user, session_id):
        session_id = require_uuid(session_id, label="session_id")
        owned = self.db.scalar(select(LearningSession.id).where(
            LearningSession.id == session_id, LearningSession.user_id == user.id
        ))
        if owned is None:
            raise NotFoundError("Session not found.")
        return list(self.db.scalars(
            select(LearnerAssessment)
            .where(LearnerAssessment.session_id == session_id)
            .order_by(LearnerAssessment.created_at, LearnerAssessment.id)
        ))

    def get(self, user, assessment_id):
        assessment = self.db.scalar(
            select(LearnerAssessment)
            .join(LearningSession, LearningSession.id == LearnerAssessment.session_id)
            .where(
                LearnerAssessment.id == require_uuid(assessment_id, label="assessment_id"),
                LearningSession.user_id == user.id,
            )
        )
        if assessment is None:
            raise NotFoundError("Assessment not found.")
        return assessment
