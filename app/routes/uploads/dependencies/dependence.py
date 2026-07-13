from functools import lru_cache

from app.adapters.storage.minio_blob_storage_adapter import (
    MinioBlobStorageAdapter,
)
from app.adapters.storage.minio_multipart_client_adapter import (
    MinioMultipartClientAdapter,
)
from app.connections.minio import get_minio_client
from app.core.uploads.abort_workflow import UploadAbortWorkflow
from app.core.uploads.complete_workflow import UploadCompletionWorkflow
from app.core.uploads.workflow import UploadInitializationWorkflow
from app.repositories.in_memory_upload_metadata_repository import (
    InMemoryUploadMetadataRepository,
)
from app.routes.uploads.controllers.controller import UploadController
from app.routes.uploads.services.service import UploadService
from app.settings.setting import get_settings


@lru_cache
def get_upload_controller() -> UploadController:
    """Build and return the configured upload controller.

    Returns:
        Fully configured upload controller.
    """
    settings = get_settings()
    minio_client = get_minio_client(settings=settings)

    multipart_client = MinioMultipartClientAdapter(
        client=minio_client,
    )
    storage_adapter = MinioBlobStorageAdapter(
        client=minio_client,
        multipart_client=multipart_client,
        bucket_name=settings.minio.bucket_name,
        signed_url_expires_seconds=(
            settings.upload.signed_url_expires_seconds
        ),
    )
    repository = InMemoryUploadMetadataRepository()

    init_workflow = UploadInitializationWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
        config=settings.upload,
    )
    complete_workflow = UploadCompletionWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )
    abort_workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )
    service = UploadService(
        init_workflow=init_workflow,
        complete_workflow=complete_workflow,
        abort_workflow=abort_workflow,
    )

    return UploadController(service=service)
