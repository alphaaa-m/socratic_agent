"""Conversation memory -- Phase 4 (docs Sec 14.7)."""

from langchain_core.messages import AIMessage, HumanMessage


class ConversationMemory:
    def __init__(self, gateway=None):
        self.gateway = gateway

    def window(self, turn, state) -> list:
        """Return the newest ten persisted messages as LangChain chat messages."""
        messages = []
        for message in turn.history[-10:]:
            content = message.get("content", "")
            if message.get("sender") == "student":
                messages.append(HumanMessage(content=content))
            elif message.get("sender") == "agent":
                messages.append(AIMessage(content=content))
        return messages

    def retrieval_query(self, turn, state) -> str:
        """Use the session goal and newest student text, constrained for retrieval."""
        latest = turn.student_message
        if not latest:
            for message in reversed(turn.history):
                if message.get("sender") == "student":
                    latest = message.get("content", "")
                    break
        core_question = state.core_question or ""
        return f"{core_question} {latest}".strip()[:500]
