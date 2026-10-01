from uuid import UUID

from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.datasets.dtos.dto import (
    DatasetDeleteResponseDataDTO,
    DatasetDeleteResponseDTO,
    DatasetListResponseDTO,
    DatasetResponseDTO,
)
from app.routes.datasets.services.service import DatasetService


class DatasetController:
    """Controller responsible for handling dataset API requests.

    Coordinates dataset retrieval and deletion requests by delegating
    application processing to the dataset service and building the
    standardized response DTOs returned by the route layer.

    Attributes:
        service: Service responsible for dataset use cases.
        logger: Logger used to record controller execution events.

    Args:
        service: Configured dataset service used by this controller.
        logger: Optional logger instance used by the controller.
    """

    def __init__(
        self,
        service: DatasetService,
        logger: LoggerManager | None = None,
    ) -> None:
        """Initialize the dataset controller.

        Args:
            service: Dataset service used to process dataset requests.
            logger: Optional logger used to register controller events.
        """
        self.service = service
        self.logger = logger or LOGGER


    async def list_datasets(self) -> DatasetListResponseDTO:
        """Handle a dataset listing request.

        Returns:
            Standardized response containing all available dataset metadata.
        """

        self.logger.log_info(
            "[dataset:list:controller] Received dataset listing request"
        )

        response_data = await self.service.list_datasets()

        response = DatasetListResponseDTO(
            success=True,
            message="Datasets retrieved successfully.",
            data=response_data,
        )

        self.logger.log_info(
            "[dataset:list:controller] Dataset listing response created"
        )

        return response

    async def get_dataset(
        self,
        dataset_id: UUID,
    ) -> DatasetResponseDTO:
        """Handle a dataset metadata retrieval request.

        Args:
            dataset_id: Unique identifier of the dataset to retrieve.

        Returns:
            Standardized response containing the retrieved dataset metadata.
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

    async def delete_dataset(
        self,
        dataset_id: UUID,
    ) -> DatasetDeleteResponseDTO:
        """Handle a dataset deletion request.

        Delegates the deletion operation to the dataset service and builds
        the response with the dataset final deletion state.

        Args:
            dataset_id: Unique identifier of the dataset to delete.

        Returns:
            Standardized response containing the dataset identifier,
            final status, and update timestamp.
        """
        self.logger.log_info(
            "[dataset:delete:controller] Received dataset deletion request"
        )

        result = await self.service.delete_dataset(
            dataset_id=dataset_id,
        )

        message = (
            "Dataset was already deleted."
            if result.already_deleted
            else "Dataset deleted successfully."
        )

        response_data = DatasetDeleteResponseDataDTO(
            dataset_id=result.dataset.dataset_id,
            status=result.dataset.status,
            updated_at=result.dataset.updated_at,
        )

        response = DatasetDeleteResponseDTO(
            success=True,
            message=message,
            data=response_data,
        )

        self.logger.log_info(
            "[dataset:delete:controller] Dataset deletion response created"
        )

        return response
