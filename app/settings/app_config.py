from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        app_name: Application display name.
        app_env: Current application environment.
        max_upload_size_bytes: Maximum accepted upload size in bytes.
        upload_chunk_size_bytes: Default chunk size used for multipart uploads.
        signed_url_expires_seconds: Signed URL expiration time in seconds.
    """

    app_name: str = "SQL Agents IA"
    app_env: str = "development"
    max_upload_size_bytes: int = 104_857_600
    upload_chunk_size_bytes: int = 5_242_880
    signed_url_expires_seconds: int = 3_600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


app_config = AppConfig()