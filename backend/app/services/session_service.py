"""Session service -- Phase 2 (create/list/get), Phase 6 (end) (FR-SES-*, FR-SUM-*)."""

from sqlalchemy.orm import Session


class SessionService:
    def __init__(self, db: Session, agent=None, settings=None):
        self.db = db

    def create(self, user, subject_id):
        """FR-SES-01..03: active session, initial agent_state, counters +1."""
        raise NotImplementedError("TODO(phase-2): start session with agent_state + counters")

    def list(self, user, subject_id=None, status=None, limit: int = 20, offset: int = 0):
        """FR-HIS-01: own sessions newest first."""
        raise NotImplementedError("TODO(phase-2): list own sessions with filters")

    def get(self, user, session_id):
        raise NotImplementedError("TODO(phase-2): read one own session (404 for others)")

    def end_session(self, user, session_id):
        """FR-SUM-01..04: summary LLM then one write transaction (fallback on failure)."""
        raise NotImplementedError("TODO(phase-6): end session + summary + mastery update")

    def get_summary(self, user, session_id):
        raise NotImplementedError("TODO(phase-6): read saved session summary")
