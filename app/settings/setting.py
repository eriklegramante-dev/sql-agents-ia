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


class DatabaseSettings(BaseSettings):
    url_dev: str
    url_prod: str

    model_config = {"env_prefix": "DATABASE_"}

    def get_current_url(self) -> str:
        environment = get_settings().env.environment

        if environment == Environment.PROD and self.url_prod:
            return self.url_prod
        return self.url_dev


class SentrySettings(BaseSettings):
    dns: str | None = None

    model_config = {
        "env_prefix": "SENTRY_",
        "extra": "forbid",
    }


class SecuritySettings(BaseSettings):
    secret_key: str
    jwt_algorithm: str
    jwt_exp_minutes: int

    model_config = {
        "env_prefix": "SECURITY_",
        "extra": "forbid",
    }

class AgentSettings(BaseSettings):
    default_persona_name: str = "Assistente SQL Padrão"
    default_persona_description: str = "Um agente de IA focado em auxiliar com consultas SQL de forma segura."
    default_response_style: str = "direto"
    default_language: str = "pt-BR"

    model_config = {
        "env_prefix": "AGENT_",
        "extra": "ignore",  
    }

class Settings(BaseSettings):
    env: AppEnvironmentSettings = AppEnvironmentSettings()
    security: SecuritySettings = SecuritySettings()
    database: DatabaseSettings = DatabaseSettings()
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