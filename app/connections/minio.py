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

def get_minio_signing_client(settings: Settings | None = None) -> Minio:
    """Create the client used to sign browser-facing multipart URLs.

    Args:
        settings: Optional application settings; resolved when omitted.

    Returns:
        MinIO client using public_endpoint when configured, otherwise endpoint.
        The transport scheme and region come from the shared MinIO settings.

    Client construction does not verify public endpoint reachability or CORS.
    """
    current_settings = settings or get_settings()

    return Minio(
        endpoint=(
            current_settings.minio.public_endpoint
            or current_settings.minio.endpoint
        ),
        access_key=current_settings.minio.access_key,
        secret_key=current_settings.minio.secret_key,
        secure=current_settings.minio.secure,
        region=current_settings.minio.region,
    )