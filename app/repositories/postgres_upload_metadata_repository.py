from typing import Any

from uuid import UUID

from app.database.dataset_repository import DatasetRepository
from app.enums.dataset_status import DatasetStatus
from app.models.dataset_table import DatasetTable
from app.repositories.upload_metadata_repository import (
    UploadMetadataRepository,
)


class PostgresUploadMetadataRepository(UploadMetadataRepository):
    """
    Repository implementation responsible for persisting upload metadata
    in PostgreSQL.

    Instead of storing upload metadata in memory, this implementation
    converts the upload payload into a DatasetTable model and delegates
    persistence to DatasetRepository.
    """

    def __init__(
        self,
        dataset_repository: DatasetRepository,
    ) -> None:
        """
        Initialize the repository.

        Args:
            dataset_repository:
                Repository responsible for dataset persistence.
        """
        self.dataset_repository = dataset_repository

    async def create(
        self,
        metadata: dict[str, Any],
    ) -> None:
        """Persist initial upload metadata as a dataset owned by the caller.

        Builds a DatasetTable from the upload payload and delegates insertion
        to the dataset repository, preserving the supplied integer user_id.

        Args:
            metadata:
                Initial upload metadata containing dataset and upload identifiers,
                object key, file information, status, and trusted owner identity.

        Raises:
            KeyError:
                If a required metadata field is missing.
            ValueError:
                If the dataset status cannot be converted to the persistence enum.

        Dataset repository failures propagate to the caller.
        """

        dataset = DatasetTable(
            id=metadata["dataset_id"],
            name=metadata["dataset_name"],
            filename=metadata["filename"],
            status=DatasetStatus(metadata["dataset_status"]),
            raw_object_key=metadata["object_key"],
            prepared_object_key=None,
            user_id=metadata["user_id"],
            description=metadata.get("description"),
            file_type=None,
            content_type=metadata["content_type"],
            file_size_bytes=metadata["file_size_bytes"],
            current_upload_job_id=metadata["upload_id"],
        )

        await self.dataset_repository.create(dataset)

        return

    async def find_by_dataset_and_upload(
        self,
        dataset_id: UUID,
        upload_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve upload metadata.

        Delegates the lookup to DatasetRepository and adapts the returned
        DatasetTable model into the metadata dictionary expected by the
        upload workflows.

        Args:
            dataset_id:
                Dataset identifier.
            upload_id:
                Multipart upload identifier.

        Returns:
            Upload metadata including the persisted owner when found,
            otherwise None. Ownership is checked by the calling workflow.
        """
        dataset = await self.dataset_repository.find_by_upload(
            dataset_id=dataset_id,
            upload_id=upload_id,
        )

        if dataset is None:
            return None

        return {
            "dataset_id": str(dataset.id),
            "upload_id": dataset.current_upload_job_id,
            "object_key": dataset.raw_object_key,
            "upload_status": dataset.status.value,
            "dataset_status": dataset.status.value,
            "dataset_name": dataset.name,
            "filename": dataset.filename,
            "description": dataset.description,
            "content_type": dataset.content_type,
            "file_size_bytes": dataset.file_size_bytes,
            "user_id": dataset.user_id,
        }

    async def update_status(
        self,
        dataset_id: UUID,
        upload_id: str,
        upload_status: str,
        dataset_status: str,
    ) -> None:
        """
        Update upload metadata status.

        Delegates the upload status persistence to DatasetRepository after
        adapting the workflow values to the persistence model.

        Args:
            dataset_id:
                Dataset identifier.
            upload_id:
                Multipart upload identifier.
            upload_status:
                Upload status (kept for interface compatibility).
            dataset_status:
                Dataset status to persist.
        """

        await self.dataset_repository.update_upload_status(
            dataset_id=dataset_id,
            upload_id=upload_id,
            status=DatasetStatus(dataset_status),
        )

        return

    async def store_completed_parts(
        self,
        dataset_id: UUID,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> None:
        """
        Multipart upload parts are not persisted.

        Upload completion is represented by the dataset metadata stored in
        PostgreSQL, while multipart upload state is owned by the object
        storage provider. This method exists only to satisfy the repository
        interface.
        """
        return
