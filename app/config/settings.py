from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration loaded from defaults and environment variables.

    Centralizes database, storage backend, container names, and application
    metadata used by dependency factories.
    """

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "sql_agents"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_MIN_POOL_SIZE: int = 1
    DB_MAX_POOL_SIZE: int = 5

    STORAGE_TYPE: str = "local"
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    LOCAL_STORAGE_PATH: str = "./storage"
    RAW_CONTAINER: str = "raw"
    PREPARED_CONTAINER: str = "prepared"

    APP_NAME: str = "SQL Agents IA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        """Configures Pydantic to read environment overrides from `.env`."""

        env_file = ".env"


settings = Settings()
