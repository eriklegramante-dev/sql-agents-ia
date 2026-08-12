from datetime import datetime, timezone
from typing import Any

from app.adapters.storage.blob_storage_adapter import MultipartStorageAdapter
from app.core.uploads.enums import DatasetStatus, UploadStatus
from app.logs.setup_logger import LOGGER
from app.repositories.upload_metadata_repository import UploadMetadataRepository


class UploadAbortWorkflow:
    """Workflow responsible for aborting unfinished multipart uploads.

    Attributes:
        repository: Repository used to load and update upload metadata.
        storage_adapter: Adapter used to abort multipart uploads and cleanup parts.
        cancelable_statuses: Upload statuses that can be aborted.

    Args:
        repository: Repository used to load and update upload metadata.
        storage_adapter: Adapter used to abort multipart uploads and cleanup parts.
    """

    def __init__(
        self,
        repository: UploadMetadataRepository,
        storage_adapter: MultipartStorageAdapter,
    ) -> None:
        """Initialize the upload abort workflow.

        Args:
            repository: Repository used to load and update upload metadata.
            storage_adapter: Adapter used to abort multipart uploads and cleanup parts.
        """
        self.repository = repository
        self.storage_adapter = storage_adapter
        self.cancelable_statuses = {
            UploadStatus.UPLOADING.value,
            UploadStatus.FAILED.value,
        }

    async def run(
        self,
        dataset_id: str,
        upload_id: str,
    ) -> dict[str, Any]:
        """Run the upload abort orchestration.

        Args:
            dataset_id: Dataset identifier associated with the upload.
            upload_id: Multipart upload identifier to abort.

        Returns:
            Abort result containing dataset and upload final statuses.

        Raises:
            ValueError: If the upload does not exist or cannot be aborted.
            RuntimeError: If the storage abort or cleanup operation fails.
        """
        LOGGER.log_info("[upload:abort:workflow] Starting upload abort")

        metadata = await self.repository.find_by_dataset_and_upload(
            dataset_id=dataset_id,
            upload_id=upload_id,
        )

        if metadata is None:
            LOGGER.log_warning(
                "[upload:abort:workflow] Upload metadata not found: "
                f"dataset_id={dataset_id}, upload_id={upload_id}"
            )
            raise ValueError("Upload metadata not found.")

        current_status = metadata.get("upload_status")

        if current_status == UploadStatus.COMPLETED.value:
            LOGGER.log_warning(
                "[upload:abort:workflow] Completed upload cannot be aborted: "
                f"dataset_id={dataset_id}, upload_id={upload_id}"
            )
            raise ValueError("Completed uploads cannot be aborted.")

        if current_status == UploadStatus.ABORTED.value:
            LOGGER.log_info(
                "[upload:abort:workflow] Upload already aborted. Returning no-op response"
            )
            return {
                "dataset_id": dataset_id,
                "upload_id": upload_id,
                "upload_status": UploadStatus.ABORTED.value,
                "dataset_status": DatasetStatus.FAILED.value,
            }

        if current_status not in self.cancelable_statuses:
            LOGGER.log_warning(
                "[upload:abort:workflow] Upload status cannot be aborted: "
                f"status={current_status}"
            )
            raise ValueError("Upload status cannot be aborted.")

        object_key = metadata.get("object_key")

        if not object_key:
            raise ValueError("Upload object key not found.")

        try:
            self.storage_adapter.abort_multipart_upload(
                object_key=object_key,
                upload_id=upload_id,
            )

            self.storage_adapter.cleanup_temporary_parts(
                object_key=object_key,
                upload_id=upload_id,
            )

        except Exception as exc:
            LOGGER.log_error(
                "[upload:abort:workflow] Storage abort failed: "
                f"dataset_id={dataset_id}, upload_id={upload_id}, error={exc}"
            )

            raise RuntimeError(
                "Upload storage abort failed."
            ) from exc

        await self.repository.update_status(
            dataset_id=dataset_id,
            upload_id=upload_id,
            upload_status=UploadStatus.ABORTED.value,
            dataset_status=DatasetStatus.FAILED.value,
        )

        metadata["aborted_at"] = datetime.now(timezone.utc).isoformat()
        metadata["abort_reason"] = "User requested upload abort."

        LOGGER.log_info(
            "[upload:abort:workflow] Upload aborted successfully"
        )

        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "upload_status": UploadStatus.ABORTED.value,
            "dataset_status": DatasetStatus.FAILED.value,
        }