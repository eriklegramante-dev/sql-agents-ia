"""
Analysis HTTP route controller.

Handles incoming API requests, coordinates execution with the analysis service,
and standardizes controlled responses for business and runtime exceptions.
"""

import logging

from app.routes.analysis.dtos.dto import (
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)
from app.routes.analysis.services.service import AnalysisService

logger = logging.getLogger(__name__)


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

        Args:
            payload (AnalysisChartRequestDTO):
                Validated request payload containing chart parameters.

        Returns:
            AnalysisChartResponseDTO:
                Structured DTO indicating success or controlled error message.
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