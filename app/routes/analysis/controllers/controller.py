from app.routes.analysis.dtos.dto import (
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)
from app.routes.analysis.services.service import AnalysisService


class AnalysisController:
    """
    Controller responsible for handling chart generation requests.

    Acts as an intermediary between the HTTP route layer and the analysis
    service. It coordinates payload processing, invokes chart generation
    workflows, and formats the execution outcome into a standardized API
    response DTO.

    Attributes:
        service:
            Service instance responsible for orchestrating the analytical
            chart generation logic and validation rules.
    """

    def __init__(
        self,
        service: AnalysisService,
    ) -> None:
        """
        Initialize the AnalysisController.

        Args:
            service:
                Injected service responsible for dataset analysis and chart
                generation operations.
        """
        self.service = service

    async def generate_chart(
        self,
        request: AnalysisChartRequestDTO,
    ) -> AnalysisChartResponseDTO:
        """
        Processes a dataset chart generation request.

        Delegates the chart generation process to the underlying analysis
        service, catching validation and domain exceptions to produce a
        standardized response format.

        Args:
            request:
                Data transfer object containing the dataset identifier, chart
                specifications, or natural-language query inputs.

        Returns:
            AnalysisChartResponseDTO:
                Standardized API response containing operation success status,
                descriptive message, and structured chart visualization data
                when successful.
        """
        try:
            data = await self.service.generate_chart(request)
            return AnalysisChartResponseDTO(
                success=True,
                message="Chart generated successfully.",
                data=data,
            )
        except ValueError as exc:
            return AnalysisChartResponseDTO(
                success=False,
                message=str(exc),
                data=None,
            )