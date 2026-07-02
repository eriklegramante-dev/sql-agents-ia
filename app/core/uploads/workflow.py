from typing import Any
from uuid import uuid4

from app.adapters.storage.blob_storage_adapter import MultipartStorageAdapter
from app.core.uploads.enums import UploadStatus
from app.core.uploads.helpers.signed_parts_builder import SignedPartsBuilder
from app.core.uploads.helpers.upload_metadata_builder import UploadMetadataBuilder
from app.core.uploads.helpers.upload_plan_builder import UploadPlanBuilder
from app.core.uploads.helpers.upload_validator import UploadValidator
from app.logs.setup_logger import LOGGER
from app.repositories.upload_metadata_repository import UploadMetadataRepository
from app.routes.uploads.dtos.dto import UploadInitRequestDTO
from app.settings.setting import UploadSettings


class UploadInitializationWorkflow:
    """
    Workflow responsible for orchestrating dataset upload initialization.

    Attributes:
        repository: Repository used to persist upload metadata.
        storage_adapter: Adapter used to execute multipart upload operations.
        config: Upload configuration used for limits and chunk settings.
        validator: Helper responsible for validating upload constraints.
        plan_builder: Helper responsible for building upload planning values.
        signed_parts_builder: Helper responsible for generating signed upload URLs.
        metadata_builder: Helper responsible for building upload metadata.
    """

    def __init__(
        self,
        repository: UploadMetadataRepository,
        storage_adapter: MultipartStorageAdapter,
        config: UploadSettings,
        validator: UploadValidator | None = None,
        plan_builder: UploadPlanBuilder | None = None,
        signed_parts_builder: SignedPartsBuilder | None = None,
        metadata_builder: UploadMetadataBuilder | None = None,
    ) -> None:
        """
        Initialize the upload initialization workflow.

        Args:
            repository: Repository used to persist upload metadata.
            storage_adapter: Adapter used to execute multipart upload operations.
            config: Upload configuration used for limits and chunk settings.
            validator: Optional helper responsible for validating upload constraints.
            plan_builder: Optional helper responsible for building upload planning values.
            signed_parts_builder: Optional helper responsible for generating signed upload URLs.
            metadata_builder: Optional helper responsible for building upload metadata.
        """
        self.repository = repository
        self.storage_adapter = storage_adapter
        self.config = config
        self.validator = validator or UploadValidator(config=config)
        self.plan_builder = plan_builder or UploadPlanBuilder()
        self.signed_parts_builder = signed_parts_builder or SignedPartsBuilder(
            storage_adapter=storage_adapter,
        )
        self.metadata_builder = metadata_builder or UploadMetadataBuilder()

    def run(self, request: UploadInitRequestDTO) -> dict[str, Any]:
        """
        Run the upload initialization orchestration.

        Args:
            request: Validated upload initialization request.

        Returns:
            Upload initialization data containing identifiers and signed URLs.

        Raises:
            ValueError: If the file metadata violates upload rules.
        """
        LOGGER.log_info("[upload:init:workflow] Starting upload initialization")

        self.validator.validate(
            filename=request.filename,
            content_type=request.content_type,
            file_size_bytes=request.file_size_bytes,
        )

        dataset_id = uuid4()
        dataset_name = self.plan_builder.normalize_dataset_name(
            request.dataset_name,
        )
        object_key = self.plan_builder.generate_object_key(
            dataset_id=dataset_id,
            filename=request.filename,
        )
        chunk_size_bytes = self.config.upload_chunk_size_bytes
        chunks_count = self.plan_builder.calculate_chunks_count(
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

        parts = self.signed_parts_builder.build(
            object_key=object_key,
            upload_id=upload_id,
            chunks_count=chunks_count,
        )

        metadata = self.metadata_builder.build(
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
