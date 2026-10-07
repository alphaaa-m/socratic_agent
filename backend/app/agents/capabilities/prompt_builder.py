"""Prompt construction -- Phase 4 (docs Sec 16)."""


class PromptBuilder:
    def __init__(self, hints=None):
        self.hints = hints

    def tutor_messages(self, turn, state, learner, chunks, mode, history):
        raise NotImplementedError("TODO(phase-4): build 9-layer tutor prompt messages")
