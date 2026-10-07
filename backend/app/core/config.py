from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["local", "test", "production"] = "local"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    # "fake" is used for tests and Phase 3 (FakeGateway). Real providers from Phase 4.
    llm_provider: Literal["openai", "anthropic", "groq", "gemini", "fake"] = "fake"
    llm_model: str = "fake"
    llm_temperature: float = 0.3
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None  # Gemini via langchain-google-genai

    rag_enabled: bool = False
    faiss_index_dir: str = "./data/faiss"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_top_k: int = 4
    rag_min_score: float = 0.35
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    max_upload_mb: int = 10

    messages_per_minute: int = 20
    allow_final_reveal: bool = False

    @field_validator("database_url")
    @classmethod
    def use_psycopg3(cls, v: str) -> str:
        # Railway and Render give "postgresql://" or "postgres://" URLs.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
