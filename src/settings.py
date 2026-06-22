"""Environment / secrets loading. See .env.example for the full list of keys."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed access to environment configuration.

    Loaded once at process start. Secrets come from .env (gitignored) or the real
    environment (e.g. GitHub Actions secrets for the scheduled run).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    model_synthesis: str = Field(default="claude-opus-4-8", alias="MODEL_SYNTHESIS")
    model_screen: str = Field(default="claude-haiku-4-5-20251001", alias="MODEL_SCREEN")
    model_analysis: str = Field(default="claude-sonnet-4-6", alias="MODEL_ANALYSIS")

    # Data feeds
    fmp_api_key: str = Field(default="", alias="FMP_API_KEY")
    fmp_base_url: str = Field(
        default="https://financialmodelingprep.com/api/v3", alias="FMP_BASE_URL"
    )
    bigdata_api_key: str = Field(default="", alias="BIGDATA_API_KEY")
    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
    alphavantage_api_key: str = Field(default="", alias="ALPHAVANTAGE_API_KEY")
    financial_datasets_api_key: str = Field(default="", alias="FINANCIAL_DATASETS_API_KEY")

    # Run config
    portfolio_capital_usd: float = Field(default=10_000.0, alias="PORTFOLIO_CAPITAL_USD")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


settings = Settings()
