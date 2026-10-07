"""Progress service -- Phase 6 (FR-PRG-*)."""

from sqlalchemy.orm import Session


class ProgressService:
    def __init__(self, db: Session):
        self.db = db

    def overview(self, user):
        raise NotImplementedError("TODO(phase-6): level + strengths/weaknesses + per-subject mastery")

    def for_subject(self, user, subject_id):
        raise NotImplementedError("TODO(phase-6): mastery + score trend for one subject")

    def apply_session_result(self, user_id, subject_id, session_score: float, completed: bool):
        raise NotImplementedError("TODO(phase-6): EMA mastery update (Sec 15.6)")
