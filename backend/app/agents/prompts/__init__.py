"""Versioned prompt text for the Socratic tutor."""

from app.agents.prompts.context import (
    MEMORY_TEMPLATE,
    NO_REFERENCE_MATERIAL,
    REFERENCE_MATERIAL_TEMPLATE,
    STUDENT_CONTEXT_TEMPLATE,
    SUBJECT_CONTEXT_TEMPLATE,
)
from app.agents.prompts.modes import (
    ASK_INSTRUCTION,
    HINT_INSTRUCTIONS,
    MODE_INSTRUCTIONS,
)
from app.agents.prompts.output import OUTPUT_REQUIREMENTS
from app.agents.prompts.system import SYSTEM_PROMPT

__all__ = [
    "ASK_INSTRUCTION",
    "HINT_INSTRUCTIONS",
    "MEMORY_TEMPLATE",
    "MODE_INSTRUCTIONS",
    "NO_REFERENCE_MATERIAL",
    "OUTPUT_REQUIREMENTS",
    "REFERENCE_MATERIAL_TEMPLATE",
    "STUDENT_CONTEXT_TEMPLATE",
    "SUBJECT_CONTEXT_TEMPLATE",
    "SYSTEM_PROMPT",
]
