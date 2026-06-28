from app.adapters.storage.minio_blob_storage_adapter import (
    MinioBlobStorageAdapter,
)
from app.connections.minio import get_minio_client
from app.core.uploads.controller import UploadController
from app.core.uploads.init_workflow import UploadInitializationWorkflow
from app.core.uploads.service import UploadService
from app.repositories.in_memory_upload_metadata_repository import (
    InMemoryUploadMetadataRepository,
)
from app.settings.setting import get_settings

repository = InMemoryUploadMetadataRepository()


def get_upload_controller() -> UploadController:
    """
    Build the upload controller with its dependencies.
    """
    settings = get_settings()
    minio_client = get_minio_client(settings=settings)

    storage_adapter = MinioBlobStorageAdapter(
        client=minio_client,
        bucket_name=settings.minio.bucket_name,
        signed_url_expires_seconds=settings.upload.signed_url_expires_seconds,
    )

    workflow = UploadInitializationWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
        config=settings.upload,
    )

    service = UploadService(
        init_workflow=workflow,
    )

    return UploadController(
        service=service,
    )