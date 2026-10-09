from uuid import UUID

from app.core.datasets.models import DatasetMetadata
from app.core.datasets.repository import DatasetRepository
from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import NotFoundException


class DatasetWorkflow:
    """Workflow responsible for retrieving dataset metadata.

    The workflow belongs to the core layer and depends only on the dataset
    repository abstraction and domain models.
    """

    def __init__(
        self,
        dataset_repository: DatasetRepository,
        logger: LoggerManager | None = None,
    ) -> None:
        """Initialize the dataset retrieval workflow.

        Args:
            dataset_repository:
                Repository responsible for retrieving dataset metadata.
            logger:
                Logger used to register workflow execution events.
        """
        self.repository = dataset_repository
        self.logger = logger or LOGGER

    async def execute(
        self,
        dataset_id: UUID,
    ) -> DatasetMetadata:
        """Retrieve dataset metadata.

        Args:
            dataset_id:
                Unique identifier of the dataset.

        Returns:
            Dataset metadata represented by the core model.

        Raises:
            NotFoundException:
                If no dataset exists for the provided identifier.
        """
        self.logger.log_info(
            f"[dataset:get:workflow] Starting dataset retrieval for {dataset_id}"
        )

        dataset = await self.repository.get_metadata_by_id(
            dataset_id=dataset_id,
        )

        if dataset is None:
            raise NotFoundException(f"Dataset with ID {dataset_id} not found.")

        self.logger.log_info("[dataset:get:workflow] Dataset metadata found")

        self.logger.log_info(
            "[dataset:get:workflow] Dataset metadata retrieval completed"
        )

        return dataset