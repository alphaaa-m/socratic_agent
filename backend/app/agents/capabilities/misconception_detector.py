"""Misconception detection and normalization (docs §15.5).

The detector normalises the raw LLM label: lowercase, trim whitespace, remove
trailing punctuation, limit to 120 characters, and convert empty strings to
``None``.  It also updates the in-session misconception counter on the state
copy (the adaptive controller does the same – the detector therefore only
touches the EvaluationResult; state accounting belongs to the controller).
"""

import re

from app.agents.schemas import EvaluationResult

# Maximum length for a misconception label (§15.5)
_MAX_LABEL_LEN = 120
# Pattern matching trailing punctuation to strip
_TRAILING_PUNCT = re.compile(r"[.!?,;:]+$")


class MisconceptionDetector:
    def normalize(self, evaluation: EvaluationResult) -> EvaluationResult:
        """Return a copy of *evaluation* with the misconception label normalised.

        Steps (§15.5):
        1. Lowercase
        2. Strip leading/trailing whitespace
        3. Remove trailing punctuation (. ! ? , ; :)
        4. Truncate to 120 characters
        5. Empty string → ``None``
        """
        label = evaluation.misconception
        if label is not None:
            label = label.lower().strip()
            label = _TRAILING_PUNCT.sub("", label)
            label = label[:_MAX_LABEL_LEN] or None
        return evaluation.model_copy(update={"misconception": label})
