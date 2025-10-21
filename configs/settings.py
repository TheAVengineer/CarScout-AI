"""
Application settings
"""
import os
from pathlib import Path
from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Get project root (2 levels up from configs/settings.py)
    PROJECT_ROOT: ClassVar[Path] = Path(__file__).parent.parent
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    DATABASE_SYNC_URL: str
    
    # Redis
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Object Storage
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    S3_REGION: str = "auto"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHANNEL_BOT_TOKEN: str
    TELEGRAM_CHANNEL_ID: str
    TELEGRAM_WEBHOOK_SECRET: str
    TELEGRAM_WEBHOOK_URL: str
    
    # Telegram Channels (Three-Tier System)
    TELEGRAM_PUBLIC_CHANNEL: str  # @CarScoutBG - Free public channel
    TELEGRAM_PREMIUM_CHANNEL: str  # Premium subscribers channel ID
    TELEGRAM_VIP_CHANNEL: str  # VIP subscribers channel ID
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Stripe
    STRIPE_API_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_FREE: str
    STRIPE_PRICE_PREMIUM: str
    STRIPE_PRICE_PRO: str
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_SECRET_KEY: str
    
    # Security
    PASSWORD_HASH_SALT: str
    
    # Scraping
    SCRAPING_CONCURRENCY: int = 2
    SCRAPING_DELAY: float = 1.0
    USE_PROXY: bool = False
    PROXY_URL: str = ""
    
    # ML/AI
    PRICING_MODEL_VERSION: str = "v1"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    DEDUPE_SIMILARITY_THRESHOLD: float = 0.85
    
    # Business Rules
    CHANNEL_APPROVAL_SCORE_THRESHOLD: float = 7.5
    CHANNEL_MIN_COMP_SAMPLE_SIZE: int = 30
    CHANNEL_MIN_COMP_CONFIDENCE: float = 0.6
    FREE_PLAN_ALERT_DELAY_MINUTES: int = 30
    MAX_CHANNEL_POSTS_PER_HOUR: int = 20
    
    # Observability
    SENTRY_DSN: str = ""
    PROMETHEUS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"


# Global settings instance
settings = Settings()
