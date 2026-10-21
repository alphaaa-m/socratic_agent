"""Subject service -- Phase 2 (FR-SUB-*)."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import KnowledgeDocument, LearningSession, Subject

_NOT_SET = object()
SUBJECT_NAME_TAKEN = "A subject with this name already exists."
SUBJECT_IN_USE = "This subject cannot be deleted because it has sessions or documents. Retire it instead."


class SubjectService:
    def __init__(self, db: Session):
        self.db = db

    def list(self, active_only: bool = True) -> list[Subject]:
        """FR-SUB-01: show list of active subjects."""
        # Use a case-insensitive alphabetical order so the result does not
        # depend on whether a subject name begins with an upper- or lowercase
        # letter. The original name is a stable tie-breaker.
        statement = select(Subject).order_by(func.lower(Subject.name).asc(), Subject.name.asc())
        if active_only:
            statement = statement.where(Subject.is_active.is_(True))
        return list(self.db.scalars(statement))

    def get(self, user, subject_id) -> Subject:
        subject = self.db.get(Subject, subject_id)
        if subject is None:
            raise NotFoundError("Subject not found.")
        return subject

    def create(self, user, name: str, description: str | None = None) -> Subject:
        """FR-SUB-03: admin creates subject."""
        normalized_name = name.strip()
        if self.db.scalar(select(Subject.id).where(Subject.name == normalized_name)) is not None:
            raise ConflictError(SUBJECT_NAME_TAKEN)

        subject = Subject(name=normalized_name, description=description)
        self.db.add(subject)
        try:
            self.db.commit()
        except IntegrityError:
            # The unique constraint is authoritative for concurrent creates.
            self.db.rollback()
            raise ConflictError(SUBJECT_NAME_TAKEN) from None
        self.db.refresh(subject)
        return subject

    def update(self, user, subject_id, name=None, description=_NOT_SET, is_active=None) -> Subject:
        """FR-SUB-03: edit a subject or change its active (retired) state."""
        subject = self.get(user, subject_id)
        if name is not None:
            subject.name = name.strip()
        if description is not _NOT_SET:
            subject.description = description
        if is_active is not None:
            subject.is_active = is_active

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError(SUBJECT_NAME_TAKEN) from None
        self.db.refresh(subject)
        return subject

    def delete(self, user, subject_id) -> None:
        """FR-SUB-04: refuse when sessions or documents exist."""
        subject = self.get(user, subject_id)
        has_sessions = self.db.scalar(
            select(LearningSession.id).where(LearningSession.subject_id == subject.id).limit(1)
        )
        has_documents = self.db.scalar(
            select(KnowledgeDocument.id).where(KnowledgeDocument.subject_id == subject.id).limit(1)
        )
        if has_sessions is not None or has_documents is not None:
            raise ConflictError(SUBJECT_IN_USE)

        self.db.delete(subject)
        try:
            self.db.commit()
        except IntegrityError:
            # A session/document may have been added after the guard query.
            self.db.rollback()
            raise ConflictError(SUBJECT_IN_USE) from None
