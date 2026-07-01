from enum import Enum
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Environment(str, Enum):
    DEV = "dev"
    PROD = "prod"


class AppEnvironmentSettings(BaseSettings):
    environment: Environment = Environment.DEV

    model_config = {
        "env_prefix": "APP_",
        "extra": "forbid",
    }


class SentrySettings(BaseSettings):
    dns: str | None = None

    model_config = {
        "env_prefix": "SENTRY_",
        "extra": "forbid",
    }


class AgentSettings(BaseSettings):
    default_persona_name: str = "Standard SQL Wizard."
    default_persona_description: str = (
        "An AI agent focused on assisting with SQL queries in a secure manner."
    )
    default_response_style: str = "direct"
    default_language: str = "pt-BR"

    model_config = {
        "env_prefix": "AGENT_",
        "extra": "ignore",
    }


class UploadSettings(BaseSettings):
    max_upload_size_bytes: int = 104_857_600
    upload_chunk_size_bytes: int = 5_242_880
    signed_url_expires_seconds: int = 3_600

    model_config = {
        "extra": "ignore",
    }


class MinioSettings(BaseSettings):
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str
    secure: bool = False

    model_config = {
        "env_prefix": "MINIO_",
        "extra": "ignore",
    }


class Settings(BaseSettings):
    env: AppEnvironmentSettings = AppEnvironmentSettings()
    sentry: SentrySettings = SentrySettings()
    agent: AgentSettings = AgentSettings()
    upload: UploadSettings = UploadSettings()
    minio: MinioSettings = MinioSettings()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
