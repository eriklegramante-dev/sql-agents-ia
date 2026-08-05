from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError

from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import AppException
from app.routes.datasets.dtos.dto import (
    DatasetRequestDTO,
    DatasetResponseDTO,
)
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
        service: Optional[DatasetService] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        """Initialize the dataset controller.

        Args:
            service: Dataset service used to process requests.
            logger: Logger used to register controller execution events.
        """
        self.service = service or DatasetService()
        self.logger = logger or LOGGER

    async def get_dataset(
        self,
        dataset_id: UUID,
    ) -> dict[str, Any]:
        """Handle the dataset retrieval request.

        Args:
            dataset_id: Unique identifier of the dataset.

        Returns:
            Standardized response containing the dataset metadata.

        Raises:
            HTTPException:
                If the request validation fails or the dataset cannot be retrieved.
        """
        try:
            self.logger.log_info(
                "[dataset:get:controller] Received dataset retrieval request"
            )

            request = DatasetRequestDTO(
                dataset_id=dataset_id,
            )

            response_data = await self.service.get_dataset(
                dataset_id=request.dataset_id,
            )

            response = DatasetResponseDTO(
                success=True,
                message="Dataset retrieved successfully.",
                data=response_data,
            )

            self.logger.log_info(
                "[dataset:get:controller] Dataset retrieval response created"
            )

            return response.model_dump(mode="json")

        except ValidationError as error:
            self.logger.log_warning(
                "[dataset:get:controller] Dataset validation failed"
            )

            raise HTTPException(
                status_code=422,
                detail={
                    "success": False,
                    "message": "Invalid dataset identifier.",
                    "data": None,
                    "errors": error.errors(),
                },
            )

        except AppException as error:
            self.logger.log_error(
                "[dataset:get:controller] Dataset retrieval failed"
            )

            raise HTTPException(
                status_code=error.status_code,
                detail={
                    "success": False,
                    "message": error.message,
                    "data": None,
                    "errors": error.details,
                },
            )