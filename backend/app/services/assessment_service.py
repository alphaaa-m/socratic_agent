"""Assessment service -- Phase 5 (FR-EVA-*, FR-HIS-03)."""

from sqlalchemy.orm import Session


class AssessmentService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_session(self, user, session_id):
        raise NotImplementedError("TODO(phase-5): list assessments of own session")

    def get(self, user, assessment_id):
        raise NotImplementedError("TODO(phase-5): read one own assessment")
