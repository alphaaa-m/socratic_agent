from fastapi import APIRouter

from app.api.v1 import (
    assessments,
    auth,
    documents,
    health,
    messages,
    progress,
    sessions,
    subjects,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(subjects.router)
api_router.include_router(sessions.router)
api_router.include_router(messages.router)
api_router.include_router(assessments.router)
api_router.include_router(progress.router)
api_router.include_router(documents.router)
