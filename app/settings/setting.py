from enum import Enum
from functools import lru_cache
from pydantic import Field, field_validator

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
    """Configure storage access and browser-facing URL signing.

    Attributes:
        endpoint: SDK endpoint used for storage operations.
        access_key: Access identifier supplied to the MinIO clients.
        secret_key: Secret supplied to the MinIO clients.
        bucket_name: Bucket used for dataset objects.
        public_endpoint: Optional signing endpoint reachable by upload clients.
        region: Region supplied to the URL signing client.
        secure: Shared TLS flag used by storage and signing clients.

    Endpoint reachability, proxy routing, and CORS are not checked here.
    """
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str
    public_endpoint: str | None = None
    region: str = "us-east-1"
    secure: bool = False

    model_config = {
        "env_prefix": "MINIO_",
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


class SecuritySettings(BaseSettings):
    secret_key: str

    model_config = {
        "env_prefix": "SECURITY_",
        "extra": "ignore",
    }


class CorsSettings(BaseSettings):
    origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def origins_list(self) -> list[str]:
        """Converte a string separada por vírgulas em uma lista real sob demanda."""
        return [i.strip() for i in self.origins.split(",") if i.strip()]

    model_config = {
        "env_prefix": "CORS_",
        "extra": "ignore",
    }

class OpenAISettings(BaseSettings):
    api_key: str = ""
    model: str = "gpt-5.6-luna"

    model_config = {
        "env_prefix": "OPENAI_",
        "extra": "ignore",
    }

class Settings(BaseSettings):
    env: AppEnvironmentSettings = AppEnvironmentSettings()
    sentry: SentrySettings = SentrySettings()
    agent: AgentSettings = AgentSettings()
    upload: UploadSettings = UploadSettings()
    minio: MinioSettings = MinioSettings()
    database: DatabaseSettings = DatabaseSettings()
    storage: StorageSettings = StorageSettings()
    security: SecuritySettings = SecuritySettings()
    cors: CorsSettings = CorsSettings()
    openai: OpenAISettings = OpenAISettings()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
