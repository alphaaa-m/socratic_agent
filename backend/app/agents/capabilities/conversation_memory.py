"""Conversation memory -- Phase 4 (docs Sec 14.7)."""


class ConversationMemory:
    def __init__(self, gateway=None):
        self.gateway = gateway

    def window(self, turn, state) -> list:
        raise NotImplementedError("TODO(phase-4): last-10 message window")

    def retrieval_query(self, turn, state) -> str:
        raise NotImplementedError("TODO(phase-4): core_question + latest message (500 chars)")
