from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # OpenAI / LLM
    openai_api_key: str

    # LiveKit
    livekit_api_key: str
    livekit_api_secret: str
    livekit_url: str

    # Deepgram
    deepgram_api_key: str

    # ElevenLabs
    elevenlabs_api_key: str

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "hypnoagent"
    postgres_password: str
    postgres_db: str = "hypnoagent"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None

    # App Settings
    environment: str = "development"
    log_level: str = "INFO"
    session_ttl_seconds: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()