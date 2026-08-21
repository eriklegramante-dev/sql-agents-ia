from typing import Protocol
from uuid import UUID

from app.core.datasets.models import DatasetMetadata


class DatasetRepository(Protocol):
    """Repository abstraction for dataset metadata access.

    This interface belongs to the core layer and defines the operations
    required by dataset workflows without depending on any persistence
    implementation.
    """

    async def get_metadata_by_id(
        self,
        dataset_id: UUID,
    ) -> DatasetMetadata | None:
        """Retrieve dataset metadata by its unique identifier.

        Args:
            dataset_id: Unique identifier of the dataset.

        Returns:
            Dataset metadata when the dataset exists, otherwise None.
        """
        ...
