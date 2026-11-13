"""
Application configuration loaded from environment variables.
Never import this module from frontend code.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    secret_key: str = "change_this_in_production"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stockdb"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/stockdb"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Data Provider
    data_provider: str = "yahoo_fallback"  # upstox | kite | yahoo_fallback

    # Upstox
    upstox_api_key: Optional[str] = None
    upstox_api_secret: Optional[str] = None
    upstox_access_token: Optional[str] = None
    upstox_redirect_uri: str = "http://localhost:8000/auth/upstox/callback"

    # Kite
    kite_api_key: Optional[str] = None
    kite_api_secret: Optional[str] = None
    kite_access_token: Optional[str] = None

    # ML
    model_retrain_interval_hours: int = 24
    signal_confidence_threshold: float = 0.60
    risk_reward_ratio: float = 2.0
    atr_multiplier_sl: float = 1.5
    atr_multiplier_tp: float = 3.0

    # Data freshness (seconds)
    live_threshold_seconds: int = 30
    delayed_threshold_seconds: int = 300

    # Market hours IST
    market_open_time: str = "09:15"
    market_close_time: str = "15:30"

    # Logging
    log_level: str = "INFO"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
