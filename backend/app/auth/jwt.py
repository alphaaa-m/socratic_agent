"""JWT helpers -- implemented in Phase 1 (docs Sec 19.4.1)."""

from datetime import timedelta
from uuid import UUID


def create_token(user_id: UUID, role: str, token_type: str, lifetime: timedelta) -> str:
    raise NotImplementedError("TODO(phase-1): create HS256 JWT with sub/type/iat/exp/jti")


def decode_token(token: str, expected_type: str) -> dict:
    raise NotImplementedError("TODO(phase-1): decode JWT, verify signature/expiry/type")
