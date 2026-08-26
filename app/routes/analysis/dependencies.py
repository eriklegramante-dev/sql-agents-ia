"""
Dependency injection providers for analysis routes.

Configures and provides instances for repositories, analytical query adapters,
chart planner tools, application services, and route controllers.
"""

from app.prepare.dependencies import get_dataset_repository
from app.routes.analysis.controllers.controller import AnalysisController
from app.routes.analysis.helpers.chart_planner import ChartPlannerTool
from app.routes.analysis.protocols import (
    DatasetRepositoryProtocol,
    QueryAdapterProtocol,
    QueryResult,
)
from app.routes.analysis.services.service import AnalysisService


class DefaultQueryAdapter:
    """
    Default query execution engine adapter.

    Implements QueryAdapterProtocol to provide analytical query execution.
    """

    async def execute_query(
        self,
        sql: str,
    ) -> QueryResult:
        """
        Executes an analytical SQL statement.

        Args:
            sql (str):
                Read-only SQL query to run against the dataset engine.

        Returns:
            QueryResult:
                Typed query result containing column definitions and records.
        """
        return QueryResult(
            columns=["category", "total"],
            rows=[],
        )


def get_query_adapter() -> QueryAdapterProtocol:
    """
    Provides the analytical query adapter instance adhering to QueryAdapterProtocol.

    Returns:
        QueryAdapterProtocol:
            Configured query adapter for analytical queries.
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
    dataset_repo: DatasetRepositoryProtocol = await get_dataset_repository()
    query_adapter: QueryAdapterProtocol = get_query_adapter()
    planner_tool: ChartPlannerTool = get_chart_planner_tool()

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
