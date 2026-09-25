from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pipsentry"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # Clerk (auth)
    clerk_secret_key: str | None = None
    clerk_publishable_key: str | None = None
    clerk_jwks_url: str | None = None

    # LLM providers
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-reasoner"

    # Embeddings (Knowledge Hub ingestion — spec Section 6)
    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"

    # Local storage for uploaded knowledge sources (PDF/TXT), keyed by user/source id.
    # A single-instance MVP concern; move to S3-compatible blob storage before
    # scaling the API horizontally (Section 12 recommends this stays out of Postgres).
    uploads_dir: str = "uploads"

    # Market data (Section 3, "Market Data" row + Phase 3)
    twelvedata_api_key: str | None = None
    financial_modeling_prep_api_key: str | None = None
    # Unofficial but widely-used static JSON mirror of ForexFactory's calendar feed.
    # ForexFactory publishes no official API; this is the same feed most retail
    # tools consume. Swappable behind fetch_calendar() if it ever goes away.
    forexfactory_calendar_url: str = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

    # Telegram (Section 6/11 delivery channel — one platform bot, per-user chat id)
    telegram_bot_token: str | None = None

    # Symmetric key (Fernet, 32 url-safe base64 bytes) encrypting telegram_chat_id
    # at rest per Section 11 ("Per-user Telegram... chat IDs encrypted at rest").
    # Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
    field_encryption_key: str | None = None

    # Error tracking (Section 13) — inert until a DSN is set.
    sentry_dsn: str | None = None

    # App
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
