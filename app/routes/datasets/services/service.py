from typing import Optional
from uuid import UUID

from app.core.datasets.workflow import DatasetWorkflow
from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO


class DatasetService:
    """Service responsible for coordinating dataset retrieval operations.

    Attributes:
        workflow: Workflow responsible for executing the dataset retrieval.
        logger: Logger used to record service execution events.

    Args:
        workflow: Configured dataset workflow used by this service.
        logger: Logger instance used by this service.
    """

    def __init__(
        self,
        workflow: Optional[DatasetWorkflow] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        """Initialize the dataset service.

        Args:
            workflow: Dataset workflow responsible for retrieving metadata.
            logger: Logger used to register service execution events.
        """
        self.logger = logger or LOGGER
        self.workflow = workflow or DatasetWorkflow()

    async def get_dataset(
        self,
        dataset_id: UUID,
    ) -> DatasetResponseDataDTO:
        """Retrieve dataset metadata.

        Args:
            dataset_id: Unique identifier of the dataset.

        Returns:
            Dataset metadata returned by the workflow.
        """
        self.logger.log_info(
            f"[dataset:get:service] Starting dataset retrieval for {dataset_id}"
        )

        result = await self.workflow.execute(
            dataset_id=dataset_id,
        )

        self.logger.log_info(
            "[dataset:get:service] Dataset retrieval finished"
        )

        return result