# Security and Error Handling

*Socratic Agent project document. [Index](README.md) | [← Previous](13-testing-and-ai-evaluation.md) | [Next →](15-deployment.md)*

---

## 26. Security

| Area | Requirement and implementation |
|---|---|
| **Password hashing** | Use Argon2id (`argon2-cffi` defaults). Never log or return passwords. Enforce 8 to 128 characters with a letter and a digit. Check on login with a constant-time compare (library). Use the same error for unknown email and wrong password. |
| **JWT authentication** | HS256 with a secret of 32 bytes or more from the environment. Access token 30 minutes, refresh token 7 days. Claims: `sub`, `type`, `iat`, `exp`, `jti`. Check `type`. Load the user from the database on each request. Rotate the secret on suspicion of leak (this logs out all users). A future release can add a refresh-token store for revocation. |
| **Token storage** | The browser never sees tokens. The BFF stores them in `httpOnly`, `Secure`, `SameSite=Lax` cookies. |
| **Authorization** | Use the dependencies `get_current_user` and `require_admin`. For each resource, the service filters by `user_id`. A non-owner receives `404`. Administrators cannot read student conversations (Section 11). |
| **Input validation** | Pydantic schemas on every body and query parameter. Message length 1 to 4000. Strip control characters. Upload: allow `.pdf`, `.txt`, `.md`; check MIME type and file signature; limit size to 10 MB; never use the user's file name as a path (use a generated name). |
| **SQL injection** | Use the SQLAlchemy ORM and bound parameters only. Do not build SQL with string formatting. Code review rule: no raw SQL with user input. |
| **Prompt injection** | Put student text and retrieved text in delimiters and tell the model that they are data (Section 16). The agent has no tools and no write access, so the impact is limited to the reply text. The leak guard and output schema limit unsafe replies. Do not put secrets in prompts. |
| **API security** | HTTPS only. CORS allows only the known frontend origin. Rate limits: login 5 per minute, messages 20 per minute for each user, global default limit for each IP. Security headers on the frontend (CSP, `X-Content-Type-Options`, `Referrer-Policy`). Disable `/docs` in production. Limit request body size. Include a request ID in each log line and error. |
| **Environment variables** | Keep secrets only in environment variables or the host secret store. Commit only `.env.example`. Add `.env` to `.gitignore`. Use different secrets for local, test and production. |
| **LLM API key protection** | The key exists only in the backend environment. The browser never calls the LLM. Set a monthly spending limit in the provider console. Use a separate key for each environment. Do not log request headers. |
| **Data privacy** | Send only learning content to the LLM: no name, email or ID. Delete all user data on `DELETE /users/me`. Do not log full message text; log IDs and metrics. Encrypt the database at rest (managed service default) and in transit (TLS). Define a retention period for old sessions before launch. If students under the legal age can use the system, complete a legal review for children's data rules before release. Check the data handling terms of the LLM provider. |
| **Dependencies** | Pin versions in a lock file. Enable Dependabot or a similar tool. Run `pip-audit` and `npm audit` in CI. |
| **Logging and audit** | Log login failures, role changes, document uploads and deletions, and account deletions. Do not log secrets. |
| **Admin bootstrap** | Create the first administrator with `scripts/create_admin.py`. Never expose a public admin registration. |

---

## 27. Error Handling

### 27.1 Principles

1. Return one error format (Section 18.2) for all errors.
2. Do not show stack traces, SQL or provider messages to the client.
3. Log the full error on the server with the request ID.
4. A turn is atomic: on an error, the system saves nothing for that turn.
5. The student keeps the typed text in the UI after an error.

### 27.2 Error Situations

| Situation | Detection | System action | Client response |
|---|---|---|---|
| **Invalid input** | Pydantic validation | Reject. No side effect. | `422 VALIDATION_ERROR` with field details. |
| **Authentication failure** | Missing, expired or invalid token. Wrong credentials. | Reject. Count the failed login for the rate limit. | `401` (`UNAUTHENTICATED`, `TOKEN_EXPIRED`, `TOKEN_INVALID`). The BFF tries a refresh, then goes to login. |
| **Authorization failure** | Wrong role | Reject. Log the event. | `403 FORBIDDEN`. |
| **Database error** | `SQLAlchemyError`, connection error | Roll back. Log. Retry once for a connection error in a read phase only. | `500 INTERNAL_ERROR` (or `503` if the database is down). |
| **Unique or conflict error** | `IntegrityError` | Roll back. Map to a clear conflict. | `409 CONFLICT`. |
| **Turn conflict** | `turn_index` differs in the write phase | Roll back. Do not save. | `409 TURN_CONFLICT`. The UI reloads the messages. |
| **LLM API failure** | Provider error, invalid output | Retry two times with exponential backoff (1 s, 2 s) for `429`, `5xx` and timeouts. Repeat an invalid structured output once. After this, abort the turn. Save nothing. | `503 LLM_UNAVAILABLE`. |
| **LLM timeout** | 30-second limit | Same as above. | `504 LLM_TIMEOUT`. |
| **LLM rate limit** | Provider `429` | Backoff and retry. If still limited, abort. | `503` with `Retry-After`. |
| **Summary generation failure** | Error in the summary call | Build a fallback summary from stored data (`generated_by = "fallback"`). End the session. | `200` with the fallback summary. |
| **Leak guard failure** | Two rejected replies | Use the template question for the current concept. Log the event. | `201` with the template reply. |
| **RAG failure** | Vector store error or timeout (2 s) | Continue without chunks. Set `rag_status = "error"`. Log. | `201` (normal). The state shows `rag_status`. |
| **Empty retrieval result** | No chunk above the threshold | Use general knowledge mode. Set `rag_status = "empty"`. | `201` (normal). |
| **Document processing failure** | Exception in the background task | Delete the partial vectors. Set `failed` with `error_message`. | The status endpoint shows `failed`. |
| **Vector delete failure** | Error when deleting vectors | Keep the document row. Stop. Log. | `502` on `DELETE /documents/{id}`. The administrator can retry. |
| **Rate limit** | `slowapi` | Reject. | `429 RATE_LIMITED` with `Retry-After`. |
| **Invalid session** | Session not found, not owned | Reject. | `404 NOT_FOUND`. |
| **Session not active** | `status != 'active'` | Reject. | `409 SESSION_NOT_ACTIVE`. |
| **File too large or wrong type** | Size and type checks | Reject before processing. | `413` or `415`. |
| **Unexpected exception** | Global handler | Log with request ID. | `500 INTERNAL_ERROR` with the request ID. |

### 27.3 Implementation

```python
# app/core/exceptions.py
class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, code: str | None = None, details: list | None = None):
        self.message = message or self.message
        self.code = code or self.code
        self.details = details or []


class UnauthenticatedError(AppError): status_code, code, message = 401, "UNAUTHENTICATED", "Authentication is required."
class ForbiddenError(AppError):       status_code, code, message = 403, "FORBIDDEN", "You do not have access."
class NotFoundError(AppError):        status_code, code, message = 404, "NOT_FOUND", "Resource not found."
class ConflictError(AppError):        status_code, code, message = 409, "CONFLICT", "The request conflicts with the current state."
class SessionNotActiveError(ConflictError): code, message = "SESSION_NOT_ACTIVE", "The session is not active."
class TurnConflictError(ConflictError):     code, message = "TURN_CONFLICT", "Another request changed this session."
class LLMUnavailableError(AppError):  status_code, code, message = 503, "LLM_UNAVAILABLE", "The tutor is not available. Try again."
class LLMTimeoutError(AppError):      status_code, code, message = 504, "LLM_TIMEOUT", "The tutor took too long. Try again."


def register_exception_handlers(app):
    @app.exception_handler(AppError)
    async def app_error_handler(request, exc: AppError):
        return error_response(request, exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(Exception)
    async def unhandled(request, exc: Exception):
        logger.exception("unhandled error", extra={"request_id": request.state.request_id})
        return error_response(request, 500, "INTERNAL_ERROR", "An unexpected error occurred.", [])
    # Also register handlers for RequestValidationError (422) and RateLimitExceeded (429).
```

```python
# app/agents/llm_gateway.py  (retry policy, outline)
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

RETRYABLE = (TimeoutError, RateLimitError, APIConnectionError, InternalServerError)  # provider exception types

@retry(retry=retry_if_exception_type(RETRYABLE), stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _call(runnable, messages):
    return runnable.invoke(messages)
```

The gateway converts the final failure to `LLMUnavailableError` or `LLMTimeoutError`. Set `max_retries=0` in the LangChain model when you use `tenacity`, so that the two layers do not multiply the retries.

---

*[Index](README.md) | [← Previous](13-testing-and-ai-evaluation.md) | [Next →](15-deployment.md)*
