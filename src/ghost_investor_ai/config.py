"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://localhost/ghost_investor_ai"

    # API Keys - Enrichment
    apollo_api_key: Optional[str] = None
    clearbit_api_key: Optional[str] = None
    people_data_labs_api_key: Optional[str] = None

    # LLM
    openai_api_key: Optional[str] = None

    # Email Integration
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    google_credentials_json: Optional[str] = "credentials.json"
    outlook_client_id: Optional[str] = None
    outlook_client_secret: Optional[str] = None

    # CRM Integration
    ghostcrm_api_key: Optional[str] = None
    ghostcrm_base_url: Optional[str] = None

    # LinkedIn (optional)
    linkedin_api_key: Optional[str] = None

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Rate Limiting
    rate_limit_email_per_hour: int = 50
    rate_limit_unique_recipients_per_day: int = 500

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend_url: str = "redis://localhost:6379/1"

    # App Config
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
