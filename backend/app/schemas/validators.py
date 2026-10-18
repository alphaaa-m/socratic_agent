"""Shared Pydantic field checks used by more than one schema."""

import re

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

_LETTER = re.compile(r"[A-Za-z]")
_DIGIT = re.compile(r"\d")


def check_password_strength(value: str) -> str:
    """FR-REG-04: 8-128 characters with at least one letter and one digit.

    Length itself is enforced by ``Field(min_length=..., max_length=...)``; this
    helper only adds the character-class rule.
    """
    if not _LETTER.search(value) or not _DIGIT.search(value):
        raise ValueError("Password must contain at least one letter and one digit.")
    return value
