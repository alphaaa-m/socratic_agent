"""Subject service -- Phase 2 (FR-SUB-*)."""

from sqlalchemy.orm import Session


class SubjectService:
    def __init__(self, db: Session):
        self.db = db

    def list(self, active_only: bool = True):
        """FR-SUB-01: show list of active subjects."""
        raise NotImplementedError("TODO(phase-2): list subjects (filter by is_active)")

    def get(self, user, subject_id):
        raise NotImplementedError("TODO(phase-2): read one subject")

    def create(self, user, name: str, description: str | None = None):
        """FR-SUB-03: admin creates subject."""
        raise NotImplementedError("TODO(phase-2): admin create subject")

    def update(self, user, subject_id, name=None, description=None, is_active=None):
        raise NotImplementedError("TODO(phase-2): admin change/retire subject")

    def delete(self, user, subject_id):
        """FR-SUB-04: refuse when sessions or documents exist."""
        raise NotImplementedError("TODO(phase-2): admin delete subject with guard")
