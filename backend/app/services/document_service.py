"""Document/RAG service -- Phase 7 (FR-DOC-*, FR-RAG-*)."""

from sqlalchemy.orm import Session


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def upload(self, user, subject_id, title, file_name, content: bytes, description=None, source=None):
        raise NotImplementedError("TODO(phase-7): validate + hash check + background ingest")

    def list(self, user, subject_id=None, status=None, limit: int = 20, offset: int = 0):
        raise NotImplementedError("TODO(phase-7): admin list documents")

    def get(self, user, document_id):
        raise NotImplementedError("TODO(phase-7): admin read document status")

    def delete(self, user, document_id):
        raise NotImplementedError("TODO(phase-7): delete vectors first, then rows (FR-DOC-05)")

    def reindex(self, user, document_id):
        raise NotImplementedError("TODO(phase-7): rebuild chunks + vectors")

    def chunks(self, user, document_id, limit: int = 20, offset: int = 0):
        raise NotImplementedError("TODO(phase-7): read document chunks")

    def search(self, user, subject_id, query: str, top_k: int = 4):
        raise NotImplementedError("TODO(phase-7): retrieval test (subject-scoped)")
