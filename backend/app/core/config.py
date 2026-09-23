from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://sana:sana_local_only@localhost:5432/sana"
    demo_auth_enabled: bool = False
    frontend_url: str = "http://localhost:5173"
    session_days: int = Field(default=7, ge=1, le=30)
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = ""
    ai_timeout_seconds: float = Field(default=25, gt=0, le=120)

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg")
        return value

    @model_validator(mode="after")
    def safe_mode(self):
        if self.app_env == "production" and self.demo_auth_enabled:
            raise ValueError("Demo authentication must be disabled in production")
        return self
