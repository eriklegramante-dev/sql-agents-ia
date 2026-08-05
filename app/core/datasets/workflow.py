from typing import Optional
from uuid import UUID

from app.database.dataset_repository import DatasetRepository
from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import NotFoundException
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO


class DatasetWorkflow:
    """Workflow responsible for retrieving dataset metadata.

    Attributes:
        repository: Repository responsible for dataset persistence operations.
        logger: Logger used to record workflow execution events.

    Args:
        dataset_repository: Repository used to retrieve dataset metadata.
        logger: Logger instance used by this workflow.
    """

    def __init__(
        self,
        dataset_repository: Optional[DatasetRepository] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        """Initialize the dataset workflow.

        Args:
            dataset_repository: Repository responsible for dataset persistence.
            logger: Logger used to register workflow execution events.
        """
        self.repository = dataset_repository or DatasetRepository()
        self.logger = logger or LOGGER

    async def execute(
        self,
        dataset_id: UUID,
    ) -> DatasetResponseDataDTO:
        """Retrieve dataset metadata.

        Args:
            dataset_id: Unique identifier of the dataset.

        Returns:
            Dataset metadata returned to the API layer.

        Raises:
            NotFoundException:
                If no dataset exists for the provided identifier.
        """
        self.logger.log_info(
            f"[dataset:get:workflow] Starting dataset retrieval for {dataset_id}"
        )

        dataset = await self.repository.get_by_id(
            dataset_id=dataset_id,
        )

        if dataset is None:
            raise NotFoundException(
                f"Dataset with ID {dataset_id} not found."
            )

        self.logger.log_info(
            "[dataset:get:workflow] Dataset metadata found"
        )

        current_status = (
            dataset.status.value
            if hasattr(dataset.status, "value")
            else str(dataset.status)
        )

        response = DatasetResponseDataDTO(
            dataset_id=dataset.id,
            name=dataset.name,
            original_filename=dataset.filename,
            content_type=dataset.content_type,
            file_size_bytes=dataset.file_size_bytes,
            status=current_status,
            object_key=dataset.raw_object_key,
            description=dataset.description,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

        self.logger.log_info(
            "[dataset:get:workflow] Dataset response created"
        )

        return response