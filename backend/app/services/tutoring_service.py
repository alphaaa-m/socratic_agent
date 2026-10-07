"""Tutoring service -- Phase 3 (docs Sec 19.5, FR-MSG-*, FR-CNV-*)."""

from sqlalchemy.orm import Session


class TutoringService:
    def __init__(self, db: Session, agent=None, settings=None):
        self.db = db
        self.agent = agent
        self.settings = settings

    def list_messages(self, user, session_id, limit: int = 50, offset: int = 0):
        """FR-CNV-02: conversation in time order with pagination."""
        raise NotImplementedError("TODO(phase-3): list session messages (owner only)")

    def handle_student_message(self, user, session_id, content: str):
        """3-phase flow: read -> agent (no DB) -> one write txn with turn_index guard."""
        raise NotImplementedError("TODO(phase-3): student message turn (409 on conflict/inactive)")

    def handle_hint_request(self, user, session_id):
        """Hint button: no assessment, saves agent hint + new state."""
        raise NotImplementedError("TODO(phase-3): hint request (raise hint_level, no assessment)")
