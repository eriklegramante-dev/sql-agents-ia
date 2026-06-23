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
    default_persona_description: str = "An AI agent focused on assisting with SQL queries in a secure manner."
    default_response_style: str = "direct"
    default_language: str = "pt-BR"

    model_config = {
        "env_prefix": "AGENT_",
        "extra": "ignore",  
    }

class Settings(BaseSettings):
    env: AppEnvironmentSettings = AppEnvironmentSettings()
    sentry: SentrySettings = SentrySettings()
    agent: AgentSettings = AgentSettings()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()