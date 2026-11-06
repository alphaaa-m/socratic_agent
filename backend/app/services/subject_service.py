"""Subject service -- Phase 2 (FR-SUB-*) plus user-owned custom subjects."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.ids import require_uuid
from app.models import KnowledgeDocument, LearningSession, Subject, User

_NOT_SET = object()
SUBJECT_NAME_TAKEN = "A subject with this name already exists."
SUBJECT_IN_USE = "This subject cannot be deleted because it has sessions or documents. Retire it instead."
DEFAULT_LOCKED = "Default subjects can only be changed by an administrator."


class SubjectService:
    def __init__(self, db: Session):
        self.db = db

    def list(self, user: User, active_only: bool = True) -> list[Subject]:
        """Show default subjects plus the caller's own custom subjects."""
        statement = (
            select(Subject)
            .where(Subject.visible_to(user.id))
            .order_by(func.lower(Subject.name).asc(), Subject.name.asc())
        )
        if active_only:
            statement = statement.where(Subject.is_active.is_(True))
        return list(self.db.scalars(statement))

    def get(self, user: User, subject_id) -> Subject:
        subject_id = require_uuid(subject_id, label="subject_id")
        subject = self.db.scalar(
            select(Subject).where(Subject.id == subject_id, Subject.visible_to(user.id))
        )
        if subject is None:
            raise NotFoundError("Subject not found.")
        return subject

    def create(self, user: User, name: str, description: str | None = None) -> Subject:
        """Any logged-in user creates a custom subject they own."""
        normalized_name = name.strip()
        if self._name_taken(normalized_name, user.id):
            raise ConflictError(SUBJECT_NAME_TAKEN)

        subject = Subject(
            name=normalized_name,
            description=description,
            owner_id=user.id,
            is_active=True,
        )
        self.db.add(subject)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError(SUBJECT_NAME_TAKEN) from None
        self.db.refresh(subject)
        return subject

    def update(self, user: User, subject_id, name=None, description=_NOT_SET, is_active=None) -> Subject:
        subject = self.get(user, subject_id)
        self._assert_can_manage(user, subject)
        if name is not None:
            normalized_name = name.strip()
            if self._name_taken(normalized_name, subject.owner_id, exclude_id=subject.id):
                raise ConflictError(SUBJECT_NAME_TAKEN)
            subject.name = normalized_name
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

    def delete(self, user: User, subject_id) -> None:
        subject = self.get(user, subject_id)
        self._assert_can_manage(user, subject)
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
            self.db.rollback()
            raise ConflictError(SUBJECT_IN_USE) from None

    def _assert_can_manage(self, user: User, subject: Subject) -> None:
        if subject.is_default:
            if user.role != "admin":
                raise ForbiddenError(DEFAULT_LOCKED)
            return
        if subject.owner_id != user.id:
            raise NotFoundError("Subject not found.")

    def _name_taken(self, name: str, owner_id: UUID | None, exclude_id: UUID | None = None) -> bool:
        statement = select(Subject.id).where(func.lower(Subject.name) == name.lower())
        if exclude_id is not None:
            statement = statement.where(Subject.id != exclude_id)
        if owner_id is None:
            statement = statement.where(Subject.owner_id.is_(None))
        else:
            statement = statement.where(Subject.owner_id == owner_id)
        return self.db.scalar(statement) is not None
