from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from app.agents.factory import build_agent
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestIdMiddleware, configure_logging
from app.core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    app.state.agent = build_agent(s)  # builds gateway, retriever, agent once
    yield


def create_app() -> FastAPI:
    s = get_settings()
    configure_logging()
    app = FastAPI(
        title="Socratic Agent API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if s.app_env == "production" else "/docs",
    )
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=s.api_prefix)
    return app


app = create_app()
