from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Anthropic (optional until Phase 5)
    anthropic_api_key: str = ""

    # OpenRouter (cheaper alternative for OCR + classification)
    openrouter_api_key: str = ""
    ocr_provider: str = "openrouter"          # "anthropic" or "openrouter"
    ocr_model: str = "qwen/qwen3.5-9b"      # OpenRouter model ID for OCR
    classifier_provider: str = "openrouter"  # "anthropic" or "openrouter"
    classifier_model: str = "deepseek/deepseek-chat-v3-0324"  # DeepSeek V3 via OpenRouter
    classifier_mode: str = "scoped"  # "scoped" (DeepSeek+Gemini debate) or "legacy" (old Haiku-only)

    # Redis
    redis_url: str = "redis://redis:6379"

    # CORS — extra allowed origins, comma-separated (e.g. Vercel preview URLs)
    cors_origins: str = ""

    # App
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
