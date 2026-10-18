"""Rate limiting (docs Sec 26). slowapi, keyed by client address by default."""

import json
from typing import Any

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


def login_rate_limit_key(request: Request) -> str:
    """Rate-limit key for login: client address + submitted email (FR-LOG-04).

    Using the email as well means one attacker hammering a single account cannot
    lock out everybody else behind the same IP address.

    slowapi calls key functions synchronously, so we cannot ``await`` the body.
    By the time the limit is checked FastAPI has already read and cached the
    JSON body, so we reuse that. Anything unexpected (no body, not JSON) simply
    falls back to the plain client address.
    """
    identity = get_remote_address(request)

    cached: Any = getattr(request, "_json", None)
    if isinstance(cached, dict):
        payload = cached
    else:
        raw = getattr(request, "_body", b"") or b""
        try:
            payload = json.loads(raw) if raw else None
        except (TypeError, ValueError):
            payload = None

    email = ""
    if isinstance(payload, dict):
        email = str(payload.get("email") or "").strip().lower()

    return f"{identity}:{email}" if email else identity
