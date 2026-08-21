from fastapi import HTTPException

from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import AppException
from app.routes.preview.dtos.dto import (
    DatasetPreviewRequestDTO,
    DatasetPreviewResponseDTO,
)
from app.routes.preview.services.service import DatasetPreviewService


class DatasetPreviewController:
    """
    Coordinates dataset preview requests.

    This controller acts as the entry point for the dataset preview feature.
    It receives validated requests from the route layer, delegates execution
    to the service layer, translates application exceptions into HTTP
    responses, and returns the standardized API response.

    The controller intentionally contains no business rules or persistence
    logic. Its responsibility is limited to request orchestration and HTTP
    response mapping, allowing the workflow to remain the single source of
    truth for dataset preview behavior.

    Attributes:
        service:
            Service responsible for coordinating dataset preview retrieval.
        logger:
            Logger manager used to record controller execution events.
    """

    def __init__(
        self,
        service: DatasetPreviewService,
        logger: LoggerManager | None = None,
    ) -> None:
        self.service = service
        self.logger = logger or LOGGER

    async def execute(
        self,
        request: DatasetPreviewRequestDTO,
    ) -> DatasetPreviewResponseDTO:
        try:
            self.logger.log_info(
                f"Starting dataset preview controller for dataset "
                f"{request.dataset_id}."
            )

            response_data = await self.service.execute(request)

            self.logger.log_info(
                f"Dataset preview controller completed for dataset "
                f"{request.dataset_id}."
            )

            return DatasetPreviewResponseDTO(
                success=True,
                message="Dataset preview retrieved successfully.",
                data=response_data,
            )

        except AppException as error:
            self.logger.log_warning(
                f"Dataset preview retrieval failed: {error.message}"
            )

            raise HTTPException(
                status_code=error.status_code,
                detail={
                    "success": False,
                    "message": error.message,
                    "data": None,
                    "errors": getattr(error, "details", None),
                },
            ) from error

        except Exception as error:
            self.logger.logger.exception(
                "Unexpected error during dataset preview retrieval."
            )

            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "message": (
                        "Internal server error during dataset preview retrieval."
                    ),
                    "data": None,
                    "errors": (["An unexpected internal error occurred."]),
                },
            ) from error
