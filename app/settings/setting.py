from pydantic_settings import BaseSettings
from functools import lru_cache
from enum import Enum
from dotenv import load_dotenv

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


class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    name: str = "sql_agents"
    user: str = "postgres"
    password: str = "password"
    min_pool_size: int = 1
    max_pool_size: int = 5

    model_config = {
        "env_prefix": "DB_",
        "extra": "ignore",
    }


class StorageSettings(BaseSettings):
    storage_type: str = "local"
    azure_storage_connection_string: str | None = None
    local_storage_path: str = "./storage"
    raw_container: str = "raw"
    prepared_container: str = "prepared"

    model_config = {
        "extra": "ignore",
    }


class Settings(BaseSettings):
    env: AppEnvironmentSettings = AppEnvironmentSettings()
    sentry: SentrySettings = SentrySettings()
    agent: AgentSettings = AgentSettings()
    database: DatabaseSettings = DatabaseSettings()
    storage: StorageSettings = StorageSettings()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
