from datetime import datetime, timezone
from typing import Any

from app.adapters.storage.blob_storage_adapter import MultipartStorageAdapter
from app.adapters.storage.exceptions import StorageOperationError
from app.core.uploads.enums import DatasetStatus, UploadStatus
from app.core.uploads.exceptions import UploadCompletionError
from app.logs.setup_logger import LOGGER
from app.repositories.upload_metadata_repository import UploadMetadataRepository


class UploadCompletionWorkflow:
    """Workflow responsible for completing multipart uploads.

    Attributes:
        repository: Persists and retrieves upload metadata during workflow execution.
        storage_adapter: Performs multipart completion operations in object storage.

    Args:
        repository: Repository instance used by this workflow.
        storage_adapter: Storage adapter instance used by this workflow.
    """

    def __init__(
        self,
        repository: UploadMetadataRepository,
        storage_adapter: MultipartStorageAdapter,
    ) -> None:
        """Initialize the upload completion workflow.

        Args:
            repository: Repository used to load and update upload metadata.
            storage_adapter: Adapter used to complete multipart uploads.
        """
        self.repository = repository
        self.storage_adapter = storage_adapter

    def run(
        self,
        dataset_id: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run the upload completion orchestration.

        Args:
            dataset_id: Dataset identifier associated with the upload.
            upload_id: Multipart upload identifier to complete.
            parts: Uploaded multipart parts received from storage.

        Returns:
            Upload completion result containing final upload metadata.

        Raises:
            ValueError: If metadata, upload status, object key, or parts are invalid.
            UploadCompletionError: If object storage cannot complete the upload.
        """
        LOGGER.log_info("[upload:complete:workflow] Starting upload completion")

        metadata = self.repository.find_by_dataset_and_upload(
            dataset_id=dataset_id,
            upload_id=upload_id,
        )

        if metadata is None:
            LOGGER.log_warning(
                "[upload:complete:workflow] Upload metadata not found: "
                f"dataset_id={dataset_id}, upload_id={upload_id}"
            )
            raise ValueError("Upload metadata not found.")

        current_status = metadata.get("upload_status")

        if current_status != UploadStatus.UPLOADING.value:
            LOGGER.log_warning(
                "[upload:complete:workflow] Upload status cannot be completed: "
                f"status={current_status}"
            )
            raise ValueError("Upload status cannot be completed.")

        object_key = metadata.get("object_key")

        if not object_key:
            raise ValueError("Upload object key not found.")

        sorted_parts = self._validate_and_sort_parts(
            parts=parts,
            expected_chunks_count=metadata.get("chunks_count"),
        )

        try:
            self.storage_adapter.complete_multipart_upload(
                object_key=object_key,
                upload_id=upload_id,
                parts=sorted_parts,
            )
        except StorageOperationError as exc:
            LOGGER.log_error(
                "[upload:complete:workflow] Storage completion failed: "
                f"dataset_id={dataset_id}, upload_id={upload_id}, error={exc}"
            )
            raise UploadCompletionError(
                "Upload completion failed in object storage."
            ) from exc

        self.repository.store_completed_parts(
            dataset_id=dataset_id,
            upload_id=upload_id,
            parts=sorted_parts,
        )
        self.repository.update_status(
            dataset_id=dataset_id,
            upload_id=upload_id,
            upload_status=UploadStatus.COMPLETED.value,
            dataset_status=DatasetStatus.COMPLETED.value,
        )

        metadata["completed_at"] = datetime.now(timezone.utc).isoformat()

        LOGGER.log_info("[upload:complete:workflow] Upload completed successfully")

        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "status": UploadStatus.COMPLETED.value,
            "object_key": object_key,
            "completed_parts_count": len(sorted_parts),
        }

    def _validate_and_sort_parts(
        self,
        parts: list[dict[str, Any]],
        expected_chunks_count: Any,
    ) -> list[dict[str, Any]]:
        """Validate and sort multipart upload parts.

        Args:
            parts: Uploaded multipart parts.
            expected_chunks_count: Expected number of chunks from metadata.

        Returns:
            Multipart parts sorted by part number.

        Raises:
            ValueError: If parts are empty, duplicated, invalid, or incomplete.
        """
        if not parts:
            raise ValueError("Upload parts must not be empty.")

        part_numbers: list[int] = []

        for part in parts:
            part_number = part.get("part_number")
            etag = part.get("etag")

            if not isinstance(part_number, int) or part_number <= 0:
                raise ValueError("Part numbers must be positive integers.")

            if not isinstance(etag, str) or not etag.strip():
                raise ValueError("Each upload part must contain a valid ETag.")

            part_numbers.append(part_number)

        if len(part_numbers) != len(set(part_numbers)):
            raise ValueError("Duplicated part numbers are not allowed.")

        if (
            expected_chunks_count is not None
            and len(parts) != expected_chunks_count
        ):
            raise ValueError(
                "Uploaded parts count does not match expected chunks count."
            )

        return sorted(parts, key=lambda part: part["part_number"])
