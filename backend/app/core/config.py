from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # App
    APP_NAME: str = "FinLit"
    DEBUG: bool = True
    API_KEY: str = "change-me"
    SECRET_KEY: str = "change-me"
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finlit:finlit_dev@db:5432/finlit"
    DATABASE_URL_SYNC: str = "postgresql://finlit:finlit_dev@db:5432/finlit"

    # AI
    AI_PROVIDER: str = "claude"  # "claude" or "openai"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Simulation defaults
    DEFAULT_ANNUAL_RETURN: float = 0.07
    DEFAULT_INFLATION_RATE: float = 0.025

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
