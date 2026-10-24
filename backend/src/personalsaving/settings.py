from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
    )

    postgres_password: SecretStr = Field(min_length=1)

    environment_name: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    external_base_url: str = "http://localhost:4455"

    postgres_user: str = "personalsaving"
    postgres_db: str = "personalsaving"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@cache
def get_settings() -> Settings:
    # Fields are populated from the environment, which mypy cannot see.
    return Settings()  # type: ignore[call-arg]
