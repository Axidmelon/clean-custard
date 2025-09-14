# File: backend/core/config.py

import logging
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with validation."""

    # Security Configuration
    secret_key: str
    access_token_expire_minutes: int = 360
    refresh_token_expire_days: int = 7
    # Database Configuration
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    frontend_url: str = "http://localhost:8080"
    backend_url: str = "http://localhost:8000"
    # External Services
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.1
    resend_api_key: str
    from_email: str
    from_name: str = "Custard AI"
    # Monitoring & Logging
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None

    # Production Settings
    environment: str = "development"
    debug: bool = False
    enable_docs: bool = True
    
    # Production Security
    allowed_origins: str = ""
    max_request_size: int = 16 * 1024 * 1024  # 16MB
    request_timeout: int = 30
    keep_alive_timeout: int = 5

    # WebSocket Configuration
    ws_heartbeat_interval: int = 30
    ws_connection_timeout: int = 300

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_redis_url: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"  # Default fallback
    redis_enabled: bool = True

    # Backup & Recovery
    backup_enabled: bool = False
    backup_schedule: str = "0 2 * * *"
    backup_retention_days: int = 30

    # LangSmith Configuration
    langsmith_api_key: str = "your-langsmith-api-key-here"
    langsmith_project: str = "clean-custard"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_tracing_enabled: bool = True

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        if not v or v == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set to a secure random string")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        valid_dbs = ["postgresql", "sqlite", "mysql"]
        if not any(db in v.lower() for db in valid_dbs):
            raise ValueError("DATABASE_URL must be a valid database URL")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v):
        if not v or v == "your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY is required")
        if not v.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must be a valid OpenAI API key")
        return v

    @field_validator("resend_api_key")
    @classmethod
    def validate_resend_key(cls, v):
        if not v or v == "your-resend-api-key-here":
            raise ValueError("RESEND_API_KEY is required")
        return v

    @field_validator("langsmith_api_key")
    @classmethod
    def validate_langsmith_key(cls, v):
        if not v or v == "your-langsmith-api-key-here":
            raise ValueError("LANGSMITH_API_KEY is required")
        return v

    @field_validator("allowed_origins")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or []

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be one of: development, staging, production")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        if v.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return v.upper()

    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


def get_settings() -> Settings:
    """Get application settings with validation."""
    try:
        settings = Settings()
        logger.info(f"Settings loaded successfully for environment: {settings.environment}")
        return settings
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise


# Global settings instance
settings = get_settings()


def validate_production_readiness() -> List[str]:
    """
    Validate that the application is ready for production.

    Returns:
        List of validation errors. Empty list means ready for production.
    """
    errors = []

    # Only run strict validation in production environment
    if settings.environment != "production":
        return errors  # Skip validation for non-production environments

    # Check critical settings
    if settings.debug:
        errors.append("DEBUG must be set to 'false' in production")

    if settings.enable_docs:
        errors.append("ENABLE_DOCS should be 'false' in production")

    # Check CORS configuration
    if not settings.allowed_origins:
        errors.append("ALLOWED_ORIGINS must be configured for production")

    if any("localhost" in origin for origin in settings.allowed_origins):
        errors.append("CORS origins should not include localhost in production")

    if settings.frontend_url.startswith("http://localhost"):
        errors.append("FRONTEND_URL should use HTTPS in production")

    if not settings.sentry_dsn:
        errors.append("SENTRY_DSN should be configured for production monitoring")

    if settings.rate_limit_enabled and not settings.rate_limit_redis_url:
        errors.append("RATE_LIMIT_REDIS_URL should be configured when rate limiting is enabled")

    # Check LangSmith configuration
    if settings.langsmith_tracing_enabled and not settings.langsmith_api_key:
        errors.append("LANGSMITH_API_KEY should be configured when tracing is enabled")

    return errors
