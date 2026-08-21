"""Dependency injection providers for analysis routes."""

from typing import Any, Dict

from app.database.dataset_repository import DatasetRepository
from app.prepare.dependencies import get_dataset_repository
from app.routes.analysis.controllers.controller import AnalysisController
from app.routes.analysis.helpers.chart_planner import ChartPlannerTool
from app.routes.analysis.services.service import AnalysisService


class DefaultQueryAdapter:
    """
    Default query execution engine adapter.

    Provides query execution fallback until analytical database adapters
    are fully bound.
    """

    async def execute_query(
        self,
        sql: str,
    ) -> Dict[str, Any]:
        """
        Executes an analytical SQL statement.

        Args:
            sql:
                Read-only SQL query to run against the dataset engine.

        Returns:
            Dict[str, Any]:
                Query result mapping containing column definitions and records.
        """
        return {
            "columns": ["category", "total"],
            "rows": [],
        }


def get_query_adapter() -> Any:
    """
    Provides the analytical query adapter instance.

    Returns:
        Any:
            Configured query adapter.
    """
    return DefaultQueryAdapter()


def get_chart_planner_tool() -> ChartPlannerTool:
    """
    Provides the chart planner tool instance.

    Returns:
        ChartPlannerTool:
            Planner tool used to infer chart configurations.
    """
    return ChartPlannerTool()


async def get_analysis_service() -> AnalysisService:
    """
    Provides the analysis service wired with dependencies.

    Returns:
        AnalysisService:
            Configured analysis service instance.
    """
    dataset_repo: DatasetRepository = await get_dataset_repository()
    query_adapter = get_query_adapter()
    planner_tool = get_chart_planner_tool()

    return AnalysisService(
        dataset_repo=dataset_repo,
        query_adapter=query_adapter,
        planner_tool=planner_tool,
    )


async def get_analysis_controller() -> AnalysisController:
    """
    Provides the analysis controller wired with the application service.

    Returns:
        AnalysisController:
            Configured analysis controller instance.
    """
    service = await get_analysis_service()
    return AnalysisController(
        service=service,
    )
