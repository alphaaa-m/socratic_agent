"""Dialogue engine incl. answer-leak guard -- Phase 4 (docs Sec 14.6)."""


class DialogueEngine:
    def __init__(self, gateway=None, settings=None):
        self.gateway = gateway
        self.settings = settings

    def generate(self, messages, state, mode, chunks=None):
        raise NotImplementedError("TODO(phase-4): generate tutor reply + answer-leak guard")

    def closing_reply(self, turn, state, evaluation=None):
        raise NotImplementedError("TODO(phase-4): closing reply for resolved sessions")
