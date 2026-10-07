"""Agent factory. Complete -- builds SocraticAgent with Fake or real gateway."""

from app.agents.llm_gateway import FakeGateway
from app.agents.socratic_agent import SocraticAgent
from app.rag.retriever import NullRetriever


def build_agent(settings, gateway=None):
    """Build the single SocraticAgent.

    `gateway` is injectable so tests can pass a FakeGateway cleanly.
    While LLM_PROVIDER=fake (Phase 0-3) the agent uses FakeGateway + NullRetriever.
    """
    gw = gateway or FakeGateway()
    retriever = NullRetriever()
    if settings.llm_provider != "fake" and gateway is None:
        raise NotImplementedError("TODO(phase-4): build LangChainGateway in factory")
    return SocraticAgent(gw, retriever, settings)
