"""Session summary generation -- Phase 6 (docs Sec 16.6.1)."""


class SessionSummarizer:
    def __init__(self, gateway=None):
        self.gateway = gateway

    def summarize(self, *args, **kwargs):
        raise NotImplementedError("TODO(phase-6): summarize session (LLM + fallback)")
