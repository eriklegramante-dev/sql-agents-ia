from typing import Any, Optional

from app.adapters.storage.minio_blob_storage_adapter import MinioBlobStorageAdapter
from app.connections.minio import get_minio_client
from app.core.uploads.abort_workflow import UploadAbortWorkflow
from app.core.uploads.complete_workflow import UploadCompletionWorkflow
from app.core.uploads.workflow import UploadInitializationWorkflow
from app.logs.setup_logger import LOGGER
from app.repositories.in_memory_upload_metadata_repository import (
    InMemoryUploadMetadataRepository,
)
from app.settings.setting import get_settings


class UploadService:
    """Service responsible for exposing upload use cases.

    Attributes:
        workflow: Main workflow alias used for upload initialization.
        init_workflow: Workflow responsible for upload initialization.
        complete_workflow: Workflow responsible for upload completion.
        abort_workflow: Workflow responsible for upload abort.

    Args:
        init_workflow: Optional initialization workflow instance used by this service.
        complete_workflow: Optional completion workflow instance used by this service.
        abort_workflow: Optional abort workflow instance used by this service.
        workflow: Optional legacy initialization workflow alias used by this service.
    """

    def __init__(
        self,
        init_workflow: Optional[UploadInitializationWorkflow] = None,
        complete_workflow: Optional[UploadCompletionWorkflow] = None,
        abort_workflow: Optional[UploadAbortWorkflow] = None,
        workflow: Optional[UploadInitializationWorkflow] = None,
    ) -> None:
        """Initialize the upload service.

        Args:
            init_workflow: Optional workflow used to initialize uploads.
            complete_workflow: Optional workflow used to complete uploads.
            abort_workflow: Optional workflow used to abort uploads.
            workflow: Optional legacy alias for the upload initialization workflow.
        """
        selected_init_workflow = init_workflow or workflow

        if (
            selected_init_workflow is not None
            or complete_workflow is not None
            or abort_workflow is not None
        ):
            self.workflow = selected_init_workflow
            self.init_workflow = self.workflow
            self.complete_workflow = complete_workflow
            self.abort_workflow = abort_workflow
            return

        repository = InMemoryUploadMetadataRepository()
        storage_adapter = self._build_storage_adapter()

        self.workflow = UploadInitializationWorkflow(
            repository=repository,
            storage_adapter=storage_adapter,
            config=get_settings().upload,
        )
        self.init_workflow = self.workflow
        self.complete_workflow = UploadCompletionWorkflow(
            repository=repository,
            storage_adapter=storage_adapter,
        )
        self.abort_workflow = UploadAbortWorkflow(
            repository=repository,
            storage_adapter=storage_adapter,
        )

    def initialize_upload(self, request: Any) -> dict[str, Any]:
        """Initialize a dataset upload.

        Args:
            request: Validated upload initialization request.

        Returns:
            Upload initialization result data.
        """
        LOGGER.log_info("[upload:init:service] Starting upload initialization")
        result = self.workflow.run(request)
        LOGGER.log_info("[upload:init:service] Upload initialization finished")
        return result

    def complete_upload(
        self,
        dataset_id: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Complete a dataset multipart upload.

        Args:
            dataset_id: Dataset identifier associated with the upload.
            upload_id: Multipart upload identifier to complete.
            parts: Uploaded multipart parts.

        Returns:
            Upload completion result data.
        """
        LOGGER.log_info("[upload:complete:service] Starting upload completion")
        result = self.complete_workflow.run(
            dataset_id=dataset_id,
            upload_id=upload_id,
            parts=parts,
        )
        LOGGER.log_info("[upload:complete:service] Upload completion finished")
        return result

    def abort_upload(self, dataset_id: str, upload_id: str) -> dict[str, Any]:
        """Abort an unfinished dataset upload.

        Args:
            dataset_id: Dataset identifier associated with the upload.
            upload_id: Multipart upload identifier to abort.

        Returns:
            Upload abort result data.
        """
        LOGGER.log_info("[upload:abort:service] Starting upload abort")
        result = self.abort_workflow.run(
            dataset_id=dataset_id,
            upload_id=upload_id,
        )
        LOGGER.log_info("[upload:abort:service] Upload abort finished")
        return result

    def _build_storage_adapter(self) -> MinioBlobStorageAdapter:
        """Build the MinIO storage adapter.

        Returns:
            Configured MinIO blob storage adapter.
        """
        settings = get_settings()
        minio_client = get_minio_client(settings=settings)

        return MinioBlobStorageAdapter(
            client=minio_client,
            bucket_name=settings.minio.bucket_name,
            signed_url_expires_seconds=settings.upload.signed_url_expires_seconds,
        )
