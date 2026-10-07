# Contributing

1. One branch per phase: `phase-N/<name>`. PR into `main`.
2. Small commits, imperative messages.
3. Follow layers (docs Sec 19.2): routers call services; services own DB/transactions; agent never imports SQLAlchemy.
4. LLM only through `LLMGateway`.
5. Tests with code; phase not done without its tests.
6. Do not change the schema (tell the instructor).
7. Do not change Pydantic schemas without approval.
8. Never commit secrets (only `.env.example`).
