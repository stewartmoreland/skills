"""Application settings.

Settings are validated once, at process start, by pydantic-settings. That is the
whole point: a missing or malformed DATABASE_URL should crash the container on
boot where a deploy pipeline will notice, not surface as an AttributeError on
`None` inside a request handler an hour later.

Read settings through `get_settings()` rather than importing a module-level
instance. The `lru_cache` makes it a singleton in production, and tests can call
`get_settings.cache_clear()` (or override the FastAPI dependency) to swap it.
"""

from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "dev", "stg", "prod"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Nested config via APP__DB__HOST style vars if you ever need it.
        env_nested_delimiter="__",
    )

    app_name: str = "service"
    environment: Environment = "local"
    log_level: str = "INFO"
    debug: bool = False

    # No default. A service that cannot reach its database has nothing useful to
    # do, so let it fail loudly at import rather than limp along.
    database_url: PostgresDsn

    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 1800
    db_echo: bool = False

    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        # Deploy systems hand this over as one comma-separated string.
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment in ("stg", "prod")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


AppSettings = Annotated[Settings, Depends(get_settings)]
