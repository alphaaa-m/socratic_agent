"""LLM model factory -- Phase 4 (docs Sec 16.7). Supports groq / gemini (/ openai / anthropic)."""

from app.core.config import Settings


def _api_key(secret):
    """Unwrap a configured SecretStr at the provider boundary only."""
    return secret.get_secret_value() if secret is not None else None


def build_chat_model(settings: Settings, temperature: float):
    """Create one provider model without importing unused provider packages.

    Tenacity owns retries in ``LangChainGateway``, so every model has its own
    retry loop disabled. This prevents one transient provider error from
    multiplying into nested retries.
    """
    common = {
        "model": settings.llm_model,
        "temperature": temperature,
        "timeout": settings.llm_timeout_seconds,
        "max_retries": 0,
    }
    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(**common, api_key=_api_key(settings.openai_api_key))
    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(**common, api_key=_api_key(settings.anthropic_api_key))
    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(**common, api_key=_api_key(settings.groq_api_key))
    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(**common, google_api_key=_api_key(settings.google_api_key))
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
