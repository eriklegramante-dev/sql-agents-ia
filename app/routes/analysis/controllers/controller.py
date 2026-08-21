from app.routes.analysis.dtos.dto import (
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)
from app.routes.analysis.services.service import AnalysisService


class AnalysisController:
    """Controller responsible for handling analysis chart endpoints."""

    def __init__(self, service: AnalysisService) -> None:
        """
        Initializes the analysis controller with the required service.

        Args:
            service:
                Business logic service for dataset analysis.
        """
        self.service = service

    async def generate_chart(
        self,
        request: AnalysisChartRequestDTO,
    ) -> AnalysisChartResponseDTO:
        """
        Delegates chart generation to the service layer and wraps the response.

        Args:
            request:
                Request DTO containing dataset identifier and parameters.

        Returns:
            AnalysisChartResponseDTO:
                Structured response DTO with chart data or error details.
        """
        try:
            data = await self.service.generate_chart(request)
            return AnalysisChartResponseDTO(
                success=True,
                message="Chart generated successfully.",
                data=data,
            )
        except ValueError as err:
            return AnalysisChartResponseDTO(
                success=False,
                message=str(err),
                data=None,
            )
        except Exception as err:
            return AnalysisChartResponseDTO(
                success=False,
                message=f"Unexpected error while generating chart: {err}",
                data=None,
            )
