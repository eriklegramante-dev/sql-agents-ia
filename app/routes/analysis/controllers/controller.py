from fastapi import HTTPException

from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import AppException
from app.routes.analysis.dtos.dto import (
    AnalysisQueryRequestDTO,
    AnalysisQueryResponseDTO,
)
from app.routes.analysis.services.service import AnalysisQueryService


class AnalysisQueryController:
    """
    Coordinates HTTP-level dataset analysis query processing.

    This controller acts as the entry point between the FastAPI route and the
    analysis application service. It delegates validated requests to the
    service, wraps successful results in the standard response structure, and
    converts predictable application exceptions into HTTP responses.

    Unexpected failures are translated into a generic internal server error
    response without exposing infrastructure or implementation details to the
    API client.

    The controller contains no dataset lookup, SQL validation, storage access,
    query execution, or analytical business rules.

    Dependencies are received through constructor injection, preventing the
    controller from instantiating its own service or logging implementation.

    Args:
        service:
            Application service responsible for coordinating the dataset
            analysis query execution flow.

        logger:
            Logger manager used to record controller execution events and
            unexpected failures.

    Attributes:
        service:
            Application service responsible for coordinating analysis query
            execution.

        logger:
            Logger manager used during controller execution.
    """

    def __init__(
        self,
        service: AnalysisQueryService,
        logger: LoggerManager | None = None,
    ) -> None:
        self.service = service
        self.logger = logger or LOGGER

    async def execute(
        self,
        request: AnalysisQueryRequestDTO,
    ) -> AnalysisQueryResponseDTO:
        """
        Execute HTTP-level dataset analysis query processing.

        Args:
            request:
                Validated analysis query request received from the route.

        Returns:
            AnalysisQueryResponseDTO:
                Standardized response envelope containing the analytical
                query result.

        Raises:
            HTTPException:
                If a predictable application error occurs or an unexpected
                internal failure prevents query execution.
        """
        try:
            self.logger.log_info(
                f"Starting analysis query controller for dataset "
                f"{request.dataset_id}."
            )

            response_data = await self.service.execute(request)

            self.logger.log_info(
                f"Analysis query controller completed for dataset "
                f"{request.dataset_id}."
            )

            return AnalysisQueryResponseDTO(
                success=True,
                message="Analysis query executed successfully.",
                data=response_data,
                errors=None,
            )

        except AppException as error:
            self.logger.log_warning(
                f"Analysis query execution failed: {error.message}"
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
                "Unexpected error during analysis query execution."
            )

            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "message": (
                        "Internal server error during analysis query "
                        "execution."
                    ),
                    "data": None,
                    "errors": [
                        "An unexpected internal error occurred."
                    ],
                },
            ) from error