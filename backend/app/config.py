from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # OpenRouter
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Firecrawl
    firecrawl_api_key: str

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "gap-analyzer"

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    # Models (OpenRouter model IDs)
    primary_model: str = "anthropic/claude-sonnet-4"
    fallback_model: str = "openai/gpt-4o-mini"
    embedding_model: str = "openai/text-embedding-3-small"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
