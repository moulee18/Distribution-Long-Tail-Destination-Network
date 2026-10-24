from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "IncuBrix Distribution Hub"
    API_V1_STR: str = "/api/v1"
    CONNECTOR_V1_STR: str = "/connector/v1"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    # Simulation mode
    SIMULATION_MODE: bool = Field(default=True)
    
    # Security & Keys
    SECRET_KEY: str = Field(default="insecure-dev-secret-key-change-in-production-min-32-bytes")
    WEBHOOK_SIGNING_SECRET: str = Field(default="incubrix-default-webhook-signing-secret")
    
    # Database (defaults to local SQLite if not set in env; Docker Compose sets PostgreSQL)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./incubrix_local.db"
    )
    DATABASE_URL_SYNC: str = Field(
        default="sqlite:///./incubrix_local.db"
    )
    
    # Redis & Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2")
    
    # MinIO / S3 Storage
    MINIO_ENDPOINT: str = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin")
    MINIO_SECURE: bool = Field(default=False)
    MINIO_BUCKET_NAME: str = Field(default="incubrix-distribution")
    
    # Local Test Platform URLs
    MOCK_PLATFORM_BASE_URL: str = Field(default="http://localhost:8001")
    LEMMY_INSTANCE_URL: str = Field(default="http://localhost:8536")
    GHOST_ADMIN_API_URL: str = Field(default="http://localhost:2368")
    PARTNER_WEBHOOK_URL: str = Field(default="http://localhost:8001/mock/webhook/receiver")
    
    # AI Provider
    AI_PROVIDER: str = Field(default="mock")
    AI_API_KEY: Optional[str] = Field(default=None)
    AI_MODEL_NAME: str = Field(default="incubrix-tailor-v1")
    
    # Rate limiting & bounds
    CONSECUTIVE_FAILURE_LIMIT: int = Field(default=5)
    CERTIFICATION_RETENTION_MINUTES: int = Field(default=10)
    RECERTIFICATION_INTERVAL_DAYS: int = Field(default=30)

settings = Settings()
