"""SocraticAgent facade -- Phase 4 (docs Sec 14.4)."""


class SocraticAgent:
    def __init__(self, gateway, retriever, settings):
        self.gateway = gateway
        self.retriever = retriever
        self.settings = settings
        # Capability wiring happens in Phase 4/5; keep attribute names stable for tests.
        self.dialogue = None
        self.evaluator = None
        self.adaptive = None
        self.levels = None
        self.hints = None
        self.memory = None
        self.prompts = None
        self.misconceptions = None
        self.summarizer = None

    def handle_turn(self, turn):
        raise NotImplementedError("TODO(phase-4): implement SocraticAgent.handle_turn pipeline")

    def summarize(self, *args, **kwargs):
        raise NotImplementedError("TODO(phase-6): implement SocraticAgent.summarize")
