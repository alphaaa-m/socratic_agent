"""Document endpoints (docs Sec 18.10) -- Phase 7 (admin only)."""

from uuid import UUID

from fastapi import APIRouter, UploadFile

from app.api.deps import DB, AdminUser
from app.schemas.common import Page
from app.schemas.document import (
    ChunkResponse,
    DocumentResponse,
    RetrievalTestRequest,
    RetrievedChunkResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=Page[DocumentResponse])
def list_documents(user: AdminUser, db: DB, limit: int = 20, offset: int = 0):
    from app.services.document_service import DocumentService

    return DocumentService(db).list(user, limit=limit, offset=offset)


@router.post("", response_model=DocumentResponse, status_code=202)
def upload_document(user: AdminUser, db: DB, file: UploadFile, subject_id: UUID, title: str):
    from app.services.document_service import DocumentService

    return DocumentService(db).upload(user, subject_id, title, file.filename, b"")


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, user: AdminUser, db: DB):
    from app.services.document_service import DocumentService

    return DocumentService(db).get(user, document_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: UUID, user: AdminUser, db: DB):
    from app.services.document_service import DocumentService

    DocumentService(db).delete(user, document_id)


@router.post("/{document_id}/reindex", response_model=DocumentResponse, status_code=202)
def reindex_document(document_id: UUID, user: AdminUser, db: DB):
    from app.services.document_service import DocumentService

    return DocumentService(db).reindex(user, document_id)


@router.get("/{document_id}/chunks", response_model=Page[ChunkResponse])
def list_chunks(document_id: UUID, user: AdminUser, db: DB, limit: int = 20, offset: int = 0):
    from app.services.document_service import DocumentService

    return DocumentService(db).chunks(user, document_id, limit, offset)


@router.post("/search", response_model=list[RetrievedChunkResponse])
def test_retrieval(body: RetrievalTestRequest, user: AdminUser, db: DB):
    from app.services.document_service import DocumentService

    return DocumentService(db).search(user, body.subject_id, body.query, body.top_k)
