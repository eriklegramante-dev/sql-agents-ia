from uuid import UUID
from typing import Optional

from fastapi import HTTPException
from pydantic import ValidationError

from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import AppException
from app.routes.schema.dtos.dto import DatasetSchemaRequestDTO, DatasetSchemaResponseDTO
from app.routes.schema.services.service import DatasetSchemaService


class DatasetSchemaController:
    """Coordinates requests for dataset schema retrieval.

    This controller acts as the entry point for the dataset schema feature
    within the application layer. It receives validated requests from the
    route, delegates the retrieval process to the service layer, and
    assembles the standardized response returned to the API.

    The controller intentionally contains no business rules or persistence
    logic. Its responsibility is limited to request orchestration and
    response construction, allowing the workflow to remain the single
    source of truth for business behavior.
    """

    def __init__(
        self,
        service: Optional[DatasetSchemaService] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        """Initializes the dataset schema controller.

        Args:
            service (DatasetSchemaService):
                Service responsible for coordinating the dataset schema
                retrieval process.
        """

        self.service = service or DatasetSchemaService()
        self.logger = logger or LOGGER

    async def get_dataset_schema(
        self,
        dataset_id: UUID,
    ) -> dict:
        """Retrieves the persisted schema for the specified dataset.

        Delegates the request to the service layer, which coordinates the
        workflow responsible for validating the dataset, loading the
        persisted schema metadata, and building the response payload.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset whose schema should be
                retrieved.

        Returns:
            DatasetSchemaResponseDTO:
                Standardized response indicating whether the operation
                succeeded and containing the requested schema metadata.
        """
        try:
            request = DatasetSchemaRequestDTO(dataset_id=dataset_id)

            self.logger.log_info(
                f"Starting dataset schema controller for dataset {request.dataset_id}."
            )

            response_data = await self.service.get_dataset_schema(request.dataset_id)

            self.logger.log_info(
                f"Dataset schema controller completed for dataset {request.dataset_id}."
            )

            return DatasetSchemaResponseDTO(
                success=True,
                message="Dataset schema retrieved successfully.",
                data=response_data,
            ).model_dump(mode="json", by_alias=True)

        except ValidationError as error:
            self.logger.log_warning(f"Invalid dataset schema request: {error.errors()}")

            raise HTTPException(
                status_code=422,
                detail={
                    "success": False,
                    "message": "Invalid dataset ID.",
                    "data": None,
                    "errors": error.errors(),
                },
            )

        except AppException as error:
            self.logger.log_warning(f"Dataset schema retrieval failed: {error.message}")

            raise HTTPException(
                status_code=error.status_code,
                detail={
                    "success": False,
                    "message": error.message,
                    "data": None,
                    "errors": error.details,
                },
            )

        except Exception as error:
            self.logger.log_error("Unexpected error during dataset schema retrieval.")

            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "message": "Internal server error during dataset schema retrieval.",
                    "data": None,
                    "errors": [str(error)],
                },
            )
