from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # App
    app_name: str = "Meeting Intelligence"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/meeting_intelligence"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Object Storage (S3-compatible)
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "meeting-intelligence"
    s3_secure: bool = False

    # LLM
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Transcription
    transcription_provider: str = "deepgram"
    deepgram_api_key: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # File retention
    file_retention_days: int = 30


settings = Settings()
