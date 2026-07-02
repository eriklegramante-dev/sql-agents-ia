from typing import Any, Optional

from app.adapters.storage.minio_blob_storage_adapter import MinioBlobStorageAdapter
from app.connections.minio import get_minio_client
from app.core.uploads.workflow import UploadInitializationWorkflow
from app.logs.setup_logger import LOGGER
from app.repositories.in_memory_upload_metadata_repository import (
    InMemoryUploadMetadataRepository,
)
from app.settings.setting import get_settings


class UploadService:
    """
    Service responsible for exposing upload use cases.
    """

    def __init__(
        self,
        workflow: Optional[UploadInitializationWorkflow] = None,
    ) -> None:
        """
        Initialize the upload service.
        """
        self.workflow = workflow or self._build_workflow()

    def initialize_upload(self, request) -> dict[str, Any]:
        """
        Initialize a dataset upload.
        """
        LOGGER.log_info("[upload:init:service] Starting upload initialization")
        result = self.workflow.run(request)
        LOGGER.log_info("[upload:init:service] Upload initialization finished")
        return result

    def _build_workflow(self) -> UploadInitializationWorkflow:
        """
        Build the upload initialization workflow dependencies.
        """
        settings = get_settings()
        minio_client = get_minio_client(settings=settings)

        storage_adapter = MinioBlobStorageAdapter(
            client=minio_client,
            bucket_name=settings.minio.bucket_name,
            signed_url_expires_seconds=settings.upload.signed_url_expires_seconds,
        )

        repository = InMemoryUploadMetadataRepository()

        return UploadInitializationWorkflow(
            repository=repository,
            storage_adapter=storage_adapter,
            config=settings.upload,
        )
