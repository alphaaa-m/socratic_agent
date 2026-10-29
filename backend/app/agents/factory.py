"""Agent factory for a deterministic test gateway or a configured provider."""

from app.agents.llm_factory import build_chat_model
from app.agents.llm_gateway import FakeGateway, LangChainGateway
from app.agents.socratic_agent import SocraticAgent
from app.rag.retriever import NullRetriever


def build_agent(settings, gateway=None):
    """Build the single SocraticAgent.

    `gateway` is injectable so tests can pass a FakeGateway cleanly.
    ``gateway`` stays injectable so all unit and API tests can remain offline.
    """
    if gateway is not None:
        gw = gateway
    elif settings.llm_provider == "fake":
        gw = FakeGateway()
    else:
        tutor_model = build_chat_model(settings, settings.llm_temperature)
        judge_model = build_chat_model(settings, 0)
        gw = LangChainGateway(tutor_model, judge_model)
    retriever = NullRetriever()
    return SocraticAgent(gw, retriever, settings)
