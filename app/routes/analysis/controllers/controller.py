from typing import Optional
#from app.adapters.duckdb_adapter import DuckDBAdapter
#from app.repositories.dataset_repository import DatasetRepository
from app.routes.analysis.dtos.dto import (
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)
from app.routes.analysis.services.service import AnalysisService


class AnalysisController:
    def __init__(
        self,
        service: Optional[AnalysisService] = None,
        dataset_repo: Optional[DatasetRepository] = None,
        query_adapter: Optional[DuckDBAdapter] = None,
    ):
        self.service = service or AnalysisService(
            dataset_repo=dataset_repo or DatasetRepository(),
            query_adapter=query_adapter or DuckDBAdapter(),
        )

    def generate_chart(self, request: AnalysisChartRequestDTO) -> AnalysisChartResponseDTO:
        try:
            data = self.service.generate_chart(request)
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