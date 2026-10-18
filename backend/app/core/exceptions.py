"""Application error types and FastAPI exception handlers (docs Sec 27.3)."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def error_response(request: Request, status: int, code: str, message: str, details: list) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": _request_id(request),
            }
        },
    )


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, code: str | None = None, details: list | None = None):
        self.message = message or self.message
        self.code = code or self.code
        self.details = details or []


class NotImplementedYet(AppError):
    status_code, code = 501, "NOT_IMPLEMENTED"


class UnauthenticatedError(AppError):
    status_code, code, message = 401, "UNAUTHENTICATED", "Authentication is required."


class BadRequestError(AppError):
    status_code, code, message = 400, "BAD_REQUEST", "The request is not valid."


class ForbiddenError(AppError):
    status_code, code, message = 403, "FORBIDDEN", "You do not have access."


class NotFoundError(AppError):
    status_code, code, message = 404, "NOT_FOUND", "Resource not found."


class ConflictError(AppError):
    status_code, code, message = 409, "CONFLICT", "The request conflicts with the current state."


class SessionNotActiveError(ConflictError):
    code, message = "SESSION_NOT_ACTIVE", "The session is not active."


class TurnConflictError(ConflictError):
    code, message = "TURN_CONFLICT", "Another request changed this session."


class LLMUnavailableError(AppError):
    status_code, code, message = 503, "LLM_UNAVAILABLE", "The tutor is not available. Try again."


class LLMTimeoutError(AppError):
    status_code, code, message = 504, "LLM_TIMEOUT", "The tutor took too long. Try again."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return error_response(request, exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(NotImplementedError)
    async def not_implemented(request: Request, exc: NotImplementedError):
        # Every unfinished Phase-0 stub becomes a clear 501 (guide Sec 0.4 Step 3).
        return error_response(request, 501, "NOT_IMPLEMENTED", str(exc) or "Not implemented yet.", [])

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"]), "issue": e["msg"]} for e in exc.errors()]
        return error_response(request, 422, "VALIDATION_ERROR", "Request validation failed.", details)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        resp = error_response(request, 429, "RATE_LIMITED", "Too many requests.", [])
        resp.headers["Retry-After"] = "60"
        return resp

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        logger.exception("unhandled error", extra={"request_id": _request_id(request)})
        return error_response(request, 500, "INTERNAL_ERROR", "An unexpected error occurred.", [])
