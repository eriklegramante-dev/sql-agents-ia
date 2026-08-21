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
        repository:
            Repository responsible for persisting upload metadata.
        storage_adapter:
            Adapter responsible for multipart upload operations.
        config:
            Upload configuration.
        validator:
            Validates upload constraints.
        plan_builder:
            Generates upload planning information.
        signed_parts_builder:
            Generates signed upload URLs.
        metadata_builder:
            Creates the upload metadata persisted by the repository.
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
        Initialize the upload workflow.

        Args:
            repository:
                Repository responsible for persisting upload metadata.
            storage_adapter:
                Storage adapter responsible for multipart upload operations.
            config:
                Upload configuration.
            validator:
                Optional upload validator.
            plan_builder:
                Optional upload planning helper.
            signed_parts_builder:
                Optional signed URL builder.
            metadata_builder:
                Optional metadata builder.
        """

        self.repository = repository
        self.storage_adapter = storage_adapter
        self.config = config

        self.validator = validator or UploadValidator(
            config=config,
        )

        self.plan_builder = plan_builder or UploadPlanBuilder()

        self.signed_parts_builder = signed_parts_builder or SignedPartsBuilder(
            storage_adapter=storage_adapter,
        )

        self.metadata_builder = metadata_builder or UploadMetadataBuilder()

    async def run(
        self,
        request: UploadInitRequestDTO,
    ) -> dict[str, Any]:
        """
        Execute the upload initialization workflow.

        This workflow validates the upload request, creates the multipart
        upload in object storage, persists the upload metadata in the
        configured repository and returns the information required by the
        frontend to upload every file chunk.

        Args:
            request:
                Validated upload initialization request.

        Returns:
            Upload initialization result.
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
            "[upload:init:workflow] Upload plan created: "
            f"dataset_id={dataset_id}, "
            f"chunks_count={chunks_count}, "
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

        await self.repository.create(metadata)

        LOGGER.log_info("[upload:init:workflow] Upload metadata persisted successfully")

        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "object_key": object_key,
            "status": UploadStatus.UPLOADING.value,
            "chunk_size_bytes": chunk_size_bytes,
            "chunks_count": chunks_count,
            "parts": parts,
        }
