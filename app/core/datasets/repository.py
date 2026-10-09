from typing import Protocol
from uuid import UUID

from app.core.datasets.models import DatasetMetadata
from app.enums.dataset_status import DatasetStatus


class DatasetRepository(Protocol):
    """Repository contract for dataset persistence operations.

    The core layer depends on this abstraction instead of a concrete database
    implementation. Database-specific logic must remain outside the core layer.
    """

    async def get_metadata_by_id(
        self,
        dataset_id: UUID,
    ) -> DatasetMetadata | None:
        """Retrieve dataset metadata by its unique identifier.

        Args:
            dataset_id:
                Unique identifier of the dataset.

        Returns:
            DatasetMetadata when the dataset exists, otherwise None.
        """
        ...

    async def list_metadata(
        self,
    ) -> list[DatasetMetadata]:
        """Retrieve metadata for all active datasets.

        Returns:
            Dataset metadata ordered from newest to oldest.
        """
        ...

    async def update_status(
        self,
        dataset_id: UUID,
        status: DatasetStatus,
        error_message: str | None = None,
    ) -> bool:
        """Update the dataset processing status.

        Args:
            dataset_id:
                Unique identifier of the dataset.
            status:
                New dataset status.
            error_message:
                Optional error message associated with the update.

        Returns:
            True when the dataset status was updated, otherwise False.
        """
        ...

    async def delete_related_records(
        self,
        dataset_id: UUID,
    ) -> None:
        """Remove persistence records associated with a dataset.

        Args:
            dataset_id:
                Unique identifier of the dataset whose related records
                should be removed.

        Raises:
            DatasetRelatedRecordsDeletionException:
                If the related-record cleanup cannot be completed.
        """
        ...