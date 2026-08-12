from uuid import UUID

from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.datasets.dtos.dto import DatasetResponseDTO
from app.routes.datasets.services.service import DatasetService


class DatasetController:
    """Controller responsible for handling dataset retrieval requests.

    Attributes:
        service: Service responsible for executing dataset retrieval use cases.
        logger: Logger used to record controller execution events.

    Args:
        service: Configured dataset service used by this controller.
        logger: Logger instance used by this controller.
    """

    def __init__(
        self,
        service: DatasetService,
        logger: LoggerManager | None = None,
    ) -> None:
        """Initialize the dataset controller.

        Args:
            service: Dataset service used to process requests.
            logger: Logger used to register controller execution events.
        """
        self.service = service
        self.logger = logger or LOGGER

    async def get_dataset(
        self,
        dataset_id: UUID,
    ) -> DatasetResponseDTO:
        """Handle the dataset retrieval request.

        Args:
            dataset_id: Unique identifier of the dataset.

        Returns:
            Standardized response containing the dataset metadata.

        Raises:
            AppException:
                If the dataset cannot be retrieved.
        """
        self.logger.log_info(
            "[dataset:get:controller] Received dataset retrieval request"
        )

        response_data = await self.service.get_dataset(
            dataset_id=dataset_id,
        )

        response = DatasetResponseDTO(
            success=True,
            message="Dataset retrieved successfully.",
            data=response_data,
        )

        self.logger.log_info(
            "[dataset:get:controller] Dataset retrieval response created"
        )

        return response