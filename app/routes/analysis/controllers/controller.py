"""
Analysis HTTP route controllers.

Handles incoming API requests, coordinates execution with the analysis services,
and standardizes controlled responses for business and runtime exceptions.
Contains both the query execution workflow (AnalysisQueryController) and
the chart generation workflow (AnalysisController).
"""

import logging
from fastapi import HTTPException

from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import AppException
from app.routes.analysis.dtos.dto import (
    AnalysisQueryRequestDTO,
    AnalysisQueryResponseDTO,
)
from app.routes.analysis.services.service import AnalysisQueryService

from app.routes.analysis.dtos.dto import (
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)
from app.routes.analysis.services.service import AnalysisService

logger = logging.getLogger(__name__)


class AnalysisQueryController:
    """
    Coordinates HTTP-level dataset analysis query processing.

    This controller acts as the entry point between the FastAPI route and the
    analysis application service. It delegates validated requests to the
    service, wraps successful results in the standard response structure, and
    converts predictable application exceptions into HTTP responses.
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
            self.logger.log_warning(f"Analysis query execution failed: {error.message}")

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
                        "Internal server error during analysis query " "execution."
                    ),
                    "data": None,
                    "errors": ["An unexpected internal error occurred."],
                },
            ) from error


class AnalysisController:
    """
    Controller handling HTTP operations for the dataset analysis module.

    Encapsulates service invocation and shields public API clients from
    internal implementation details during unexpected failures.
    """

    def __init__(self, service: AnalysisService) -> None:
        """
        Initializes the analysis controller.

        Args:
            service (AnalysisService):
                Wired analysis service instance for business execution.
        """
        self._service = service

    async def generate_chart(
        self,
        payload: AnalysisChartRequestDTO,
    ) -> AnalysisChartResponseDTO:
        """
        Handles chart generation requests with controlled error handling.

        Processes incoming requests, sanitizes validation errors, logs unexpected
        exceptions internally, and returns formatted response DTOs.
        """
        try:
            return await self._service.generate_chart(payload)
        except ValueError as err:
            logger.warning("Validation error while generating chart: %s", err)
            return AnalysisChartResponseDTO(
                success=False,
                message=str(err),
                data=None,
            )
        except Exception:
            logger.exception("Unexpected error occurred while generating chart.")
            return AnalysisChartResponseDTO(
                success=False,
                message="An internal server error occurred while processing the chart.",
                data=None,
            )
