
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Flask
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DEBUG: bool = False
    TESTING: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///dev.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES: int = 900  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES: int = 604800  # 7 days

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Stripe
    STRIPE_SECRET_KEY: str = "dev_secret_key"
    STRIPE_WEBHOOK_SECRET: str = "dev_webhook_secret"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_dev_key"

    # Email
    SENDGRID_API_KEY: str = "dev_sendgrid_key"
    SENDGRID_FROM_EMAIL: str = "noreply@opportunityfinder.com"

    # Data Source APIs
    REDDIT_CLIENT_ID: str = "dev_reddit_client_id"
    REDDIT_CLIENT_SECRET: str = "dev_reddit_secret"
    REDDIT_USER_AGENT: str = "OpportunityFinder/1.0"

    SERPAPI_KEY: str = "dev_serpapi_key"

    PRODUCT_HUNT_TOKEN: str | None = None

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Allow extra fields in .env file
    )


settings = Settings()
