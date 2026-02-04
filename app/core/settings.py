import os
from functools import lru_cache
from typing import Any, Optional

from pydantic import PostgresDsn, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Settings(BaseSettings):
    """
    Pydantic settings model to load from .env file.
    """

    model_config = SettingsConfigDict(env_file=file_path, env_file_encoding="utf-8")
    app_name: str = "IoT Onboarding & Provisioning Service"
    API_PUBLIC_V1_STR: str = "/public/v1"
    API_PRIVATE_V1_STR: str = "/private/v1"

    # Database settings here
    postgres_db: str = ""
    postgres_user: str = ""
    postgres_password: SecretStr = SecretStr("")
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_sslmode: str = "disable"

    AWS_REGION: str = "eu-west-1"
    IOT_POLICY_NAME: str = ""
    ADMIN_API_KEY: str = ""

    sqlalchemy_postgres_uri: Optional[PostgresDsn] = None

    @field_validator("sqlalchemy_postgres_uri", mode="after")
    def assemble_postgres_connection(cls, v: Optional[str], values: ValidationInfo) -> Any:  # noqa: N805
        if isinstance(v, str):
            # print("Loading SQLALCHEMY_DATABASE_URI from ...")
            return v
        # print("Creating SQLALCHEMY_DATABASE_URI from env variables ...")
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=values.data.get("postgres_host"),
            port=values.data.get("postgres_port"),
            username=values.data.get("postgres_user"),
            password=values.data.get("postgres_password").get_secret_value(),
            path=f"{values.data.get('postgres_db') or ''}",
            # query=f"sslmode={values.data.get('postgres_sslmode')}",
        )


@lru_cache()
def get_settings() -> Settings:
    """
    FastAPI dependency to get settings.
    Uses lru_cache to load only once.
    """
    return Settings()
