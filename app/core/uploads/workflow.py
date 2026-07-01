from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.adapters.storage.blob_storage_adapter import BlobStorageAdapter
from app.routes.uploads.dto import (
    UploadInitRequestDTO,
    UploadSignedPartDTO,
)
from app.core.uploads.enums import DatasetStatus, UploadStatus
from app.logs.setup_logger import LOGGER
from app.repositories.upload_metadata_repository import UploadMetadataRepository
from app.settings.setting import UploadSettings


class UploadInitializationWorkflow:
    """Workflow responsible for initializing dataset file uploads.

    Attributes:
        repository: Repository used to persist upload metadata.
        storage_adapter: Adapter used to execute blob storage operations.
        config: Application configuration used for upload limits.
        allowed_extensions: File extensions accepted by the POC.
        accepted_content_types: MIME types accepted by the POC.
    """

    def __init__(
        self,
        repository: UploadMetadataRepository,
        storage_adapter: BlobStorageAdapter,
        config: UploadSettings,
    ) -> None:
        """Initialize the upload initialization workflow.

        Args:
            repository: Repository used to persist upload metadata.
            storage_adapter: Adapter used to execute blob storage operations.
            config: Application configuration used for upload limits.
        """
        self.repository = repository
        self.storage_adapter = storage_adapter
        self.config = config
        self.allowed_extensions = {".csv", ".xlsx"}
        self.accepted_content_types = {
            "text/csv",
            "application/csv",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

    def run(self, request: UploadInitRequestDTO) -> dict[str, Any]:
        """Run the upload initialization process.

        Args:
            request: Validated upload initialization request.

        Returns:
            Upload initialization data containing identifiers and signed URLs.

        Raises:
            ValueError: If the file metadata violates upload rules.
        """
        LOGGER.log_info("[upload:init:workflow] Starting upload initialization")
        self._validate_file_extension(request.filename)
        self._validate_content_type(request.content_type)
        self._validate_file_size(request.file_size_bytes)

        dataset_id = uuid4()
        dataset_name = self._normalize_dataset_name(request.dataset_name)
        object_key = self._generate_object_key(dataset_id, request.filename)
        chunk_size_bytes = self.config.upload_chunk_size_bytes
        chunks_count = self._calculate_chunks_count(
            file_size_bytes=request.file_size_bytes,
            chunk_size_bytes=chunk_size_bytes,
        )

        LOGGER.log_debug(
            "[upload:init:workflow] Upload plan calculated: "
            f"dataset_id={dataset_id}, chunks_count={chunks_count}, "
            f"chunk_size_bytes={chunk_size_bytes}"
        )

        upload_id = self.storage_adapter.initialize_multipart_upload(
            object_key=object_key,
            content_type=request.content_type,
        )

        parts = self._generate_signed_parts(
            object_key=object_key,
            upload_id=upload_id,
            chunks_count=chunks_count,
        )

        metadata = self._build_metadata(
            dataset_id=dataset_id,
            upload_id=upload_id,
            filename=request.filename,
            content_type=request.content_type,
            file_size_bytes=request.file_size_bytes,
            dataset_name=dataset_name,
            description=request.description,
            object_key=object_key,
            chunk_size_bytes=chunk_size_bytes,
            chunks_count=chunks_count,
        )

        self.repository.create(metadata)
        LOGGER.log_info(
            "[upload:init:workflow] Upload metadata persisted successfully"
        )

        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "object_key": object_key,
            "status": UploadStatus.UPLOADING.value,
            "chunk_size_bytes": chunk_size_bytes,
            "chunks_count": chunks_count,
            "parts": parts,
        }

    def _validate_file_extension(self, filename: str) -> None:
        """Validate whether the file extension is accepted.

        Args:
            filename: Original file name.

        Raises:
            ValueError: If the extension is not allowed.
        """
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            LOGGER.log_warning(
                f"[upload:init:workflow] Invalid file extension: {extension}"
            )
            raise ValueError("Invalid file extension. Allowed: csv, xlsx.")

    def _validate_content_type(self, content_type: str) -> None:
        """Validate whether the content type is accepted.

        Args:
            content_type: Uploaded file MIME type.

        Raises:
            ValueError: If the content type is not accepted.
        """
        if content_type not in self.accepted_content_types:
            LOGGER.log_warning(
                f"[upload:init:workflow] Invalid content type: {content_type}"
            )
            raise ValueError("Invalid content type for upload.")

    def _validate_file_size(self, file_size_bytes: int) -> None:
        """Validate whether the file size is within configured limits.

        Args:
            file_size_bytes: File size in bytes.

        Raises:
            ValueError: If the file size exceeds the configured limit.
        """
        if file_size_bytes > self.config.max_upload_size_bytes:
            LOGGER.log_warning(
                "[upload:init:workflow] File size exceeds limit: "
                f"file_size_bytes={file_size_bytes}, "
                f"max_upload_size_bytes={self.config.max_upload_size_bytes}"
            )
            raise ValueError("File size exceeds the maximum upload limit.")

    def _normalize_dataset_name(self, dataset_name: str) -> str:
        """Normalize the dataset name.

        Args:
            dataset_name: Original dataset name.

        Returns:
            Normalized dataset name.
        """
        return " ".join(dataset_name.strip().split())

    def _generate_object_key(self, dataset_id: UUID, filename: str) -> str:
        """Generate the raw object key for blob storage.

        Args:
            dataset_id: Generated dataset identifier.
            filename: Original file name.

        Returns:
            Predictable object key for the raw uploaded file.
        """
        safe_filename = Path(filename).name
        return f"datasets/{dataset_id}/raw/{safe_filename}"

    def _calculate_chunks_count(
        self,
        file_size_bytes: int,
        chunk_size_bytes: int,
    ) -> int:
        """Calculate the expected amount of chunks.

        Args:
            file_size_bytes: Total file size in bytes.
            chunk_size_bytes: Chunk size in bytes.

        Returns:
            Number of chunks expected for the upload.
        """
        return ceil(file_size_bytes / chunk_size_bytes)

    def _generate_signed_parts(
        self,
        object_key: str,
        upload_id: str,
        chunks_count: int,
    ) -> list[UploadSignedPartDTO]:
        """Generate signed upload URLs for all expected chunks.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
            chunks_count: Expected amount of chunks.

        Returns:
            Signed part URLs for the frontend.
        """
        return [
            UploadSignedPartDTO(
                part_number=part_number,
                upload_url=self.storage_adapter.generate_signed_part_url(
                    object_key=object_key,
                    upload_id=upload_id,
                    part_number=part_number,
                ),
            )
            for part_number in range(1, chunks_count + 1)
        ]

    def _build_metadata(
        self,
        dataset_id: UUID,
        upload_id: str,
        filename: str,
        content_type: str,
        file_size_bytes: int,
        dataset_name: str,
        description: str | None,
        object_key: str,
        chunk_size_bytes: int,
        chunks_count: int,
    ) -> dict[str, Any]:
        """Build the initial upload metadata payload.

        Args:
            dataset_id: Generated dataset identifier.
            upload_id: Multipart upload identifier.
            filename: Original file name.
            content_type: Uploaded file MIME type.
            file_size_bytes: Total file size in bytes.
            dataset_name: Normalized dataset name.
            description: Optional dataset description.
            object_key: Raw file object key.
            chunk_size_bytes: Chunk size in bytes.
            chunks_count: Expected chunks count.

        Returns:
            Initial upload metadata.
        """
        current_time = datetime.now(timezone.utc).isoformat()

        return {
            "dataset_id": str(dataset_id),
            "upload_id": upload_id,
            "filename": filename,
            "content_type": content_type,
            "file_size_bytes": file_size_bytes,
            "dataset_name": dataset_name,
            "description": description,
            "object_key": object_key,
            "chunk_size_bytes": chunk_size_bytes,
            "chunks_count": chunks_count,
            "upload_status": UploadStatus.UPLOADING.value,
            "dataset_status": DatasetStatus.UPLOADING.value,
            "created_at": current_time,
            "updated_at": current_time,
        }
