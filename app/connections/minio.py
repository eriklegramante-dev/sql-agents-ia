from minio import Minio

from app.settings.setting import Settings, get_settings


def get_minio_client(settings: Settings | None = None) -> Minio:
    """
    Create a MinIO client using application settings.
    """
    current_settings = settings or get_settings()

    return Minio(
        endpoint=current_settings.minio.endpoint,
        access_key=current_settings.minio.access_key,
        secret_key=current_settings.minio.secret_key,
        secure=current_settings.minio.secure,
    )
