from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # OpenAI / LLM
    openai_api_key: Optional[str] = None

    # LiveKit
    livekit_api_key: Optional[str] = None
    livekit_api_secret: Optional[str] = None
    livekit_url: Optional[str] = None

    # Deepgram
    deepgram_api_key: Optional[str] = None

    # ElevenLabs
    elevenlabs_api_key: Optional[str] = None

    # Database - Supabase connection string (takes precedence)
    supabase_db_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # OR local PostgreSQL (fallback only)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "hypnoagent"
    postgres_password: str = ""
    postgres_db: str = "hypnoagent"

    # NOTE: Redis and Qdrant no longer needed!
    # - Redis → Replaced by PostgreSQL sessions table
    # - Qdrant → Replaced by Supabase pgvector
    # Kept for backward compatibility only
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    redis_password: Optional[str] = None
    qdrant_host: Optional[str] = None
    qdrant_port: Optional[int] = None
    qdrant_api_key: Optional[str] = None

    # App Settings
    environment: str = "development"
    log_level: str = "INFO"
    session_ttl_seconds: int = 3600

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()