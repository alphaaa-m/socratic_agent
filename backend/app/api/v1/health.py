from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DB
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DB):
    result = {"status": "ok", "database": "ok", "vector_store": "disabled"}
    if get_settings().rag_enabled:
        result["vector_store"] = "ok"
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        result.update(status="error", database="error")
        return JSONResponse(result, status_code=503)
    return result
