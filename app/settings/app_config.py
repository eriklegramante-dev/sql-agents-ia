from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.setting import Environment, get_settings


class AppConfig(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    app_name: str = "SQL Agents IA"
    app_env: str = "development"
    max_upload_size_bytes: int = 104_857_600
    upload_chunk_size_bytes: int = 5_242_880
    signed_url_expires_seconds: int = 3_600

    minio_endpoint: str = "127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "sql-agents-raw"
    minio_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    def get_root_path(self) -> str:
        """
        Return the application root path.
        """
        if get_settings().env.environment == Environment.PROD:
            return "/crud/prod"
        return ""


app_config = AppConfig()