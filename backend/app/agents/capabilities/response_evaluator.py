"""Response evaluation -- Phase 5 (docs Sec 16.6)."""


class ResponseEvaluator:
    def __init__(self, gateway=None):
        self.gateway = gateway

    def evaluate(self, turn, state):
        raise NotImplementedError("TODO(phase-5): call gateway.evaluate with eval prompt")
