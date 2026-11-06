"""UUID helpers. PostgreSQL stores user and resource IDs as UUID, never integers."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.exceptions import BadRequestError


def parse_uuid(value: Any, *, label: str = "id") -> uuid.UUID:
    """Return a UUID and reject numeric identifiers that PostgreSQL cannot use."""
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, (bool, int)):
        raise TypeError(f"{label} must be a UUID, not a numeric id")
    try:
        parsed = uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{label} must be a UUID") from exc
    return parsed


def require_uuid(value: Any, *, label: str = "id") -> uuid.UUID:
    """Parse a UUID or raise a 400-level application error."""
    try:
        return parse_uuid(value, label=label)
    except ValueError as exc:
        raise BadRequestError(str(exc)) from exc
