"""JWT helpers (docs Sec 19.4.1 and Sec 26). Implemented in Phase 1 (FR-JWT-*).

Two kinds of token exist:

* **access** token  -- short lived (30 min). Sent by the BFF on every API call.
* **refresh** token -- long lived (7 days). Only used against ``POST /auth/refresh``.

Every token carries the claims ``sub`` (user id), ``role``, ``type``, ``iat``,
``exp`` and ``jti``. The ``type`` claim is what stops a refresh token from being
used as an access token.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import get_settings
from app.core.exceptions import UnauthenticatedError

ACCESS = "access"
REFRESH = "refresh"

# Claims that every token must contain (FR-JWT-03).
_REQUIRED_CLAIMS = ("sub", "role", "type", "iat", "exp", "jti")


def create_token(user_id: uuid.UUID, role: str, token_type: str, lifetime: timedelta) -> str:
    """Create a signed HS256 token for one user."""
    if token_type not in (ACCESS, REFRESH):
        raise ValueError("token_type must be 'access' or 'refresh'")
    settings = get_settings()
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "iat": issued_at,
        "exp": issued_at + lifetime,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Verify a token and return its claims.

    Raises ``UnauthenticatedError`` with code ``TOKEN_EXPIRED`` when the token is
    still well formed but past its expiry, and ``TOKEN_INVALID`` for everything
    else (bad signature, wrong type, missing claims, not a UUID).
    """
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
        )
    except ExpiredSignatureError:
        raise UnauthenticatedError(
            "Your session has expired. Please sign in again.", code="TOKEN_EXPIRED"
        ) from None
    except InvalidTokenError:
        raise UnauthenticatedError("Your session token is not valid.", code="TOKEN_INVALID") from None

    missing = [claim for claim in _REQUIRED_CLAIMS if claim not in payload]
    if (
        missing
        or expected_type not in (ACCESS, REFRESH)
        or payload.get("type") != expected_type
        or payload.get("role") not in ("student", "admin")
        or not isinstance(payload.get("jti"), str)
        or not payload.get("jti")
    ):
        raise UnauthenticatedError(
            f"A valid {expected_type} token is required.", code="TOKEN_INVALID"
        )

    try:
        uuid.UUID(str(payload["sub"]))
    except (TypeError, ValueError):
        raise UnauthenticatedError("Your session token is not valid.", code="TOKEN_INVALID") from None

    return payload
