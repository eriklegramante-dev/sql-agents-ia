"""
Analysis service implementation.

Orchestrates chart planning, analytical query generation, SQL security
validation, and chart specification construction.
"""

from app.enums.chart_type import ChartType
from app.enums.dataset_status import DatasetStatus
from app.routes.analysis.dtos.dto import (
    AnalysisChartDataDTO,
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)
from app.routes.analysis.helpers.chart_builder import ChartSpecBuilder
from app.routes.analysis.helpers.chart_planner import ChartPlannerTool
from app.routes.analysis.protocols import (
    DatasetRepositoryProtocol,
    QueryAdapterProtocol,
)
from app.security.sql_validator import validate_safe_select_query


class AnalysisService:
    """
    Application service managing analytical chart generation.

    Coordinates dataset state verification, natural language query planning,
    safe SQL validation, execution via query adapters, and spec assembly.
    """

    def __init__(
        self,
        dataset_repo: DatasetRepositoryProtocol,
        query_adapter: QueryAdapterProtocol,
        planner_tool: ChartPlannerTool,
    ) -> None:
        """
        Initializes the analysis service with mandatory dependencies.

        Args:
            dataset_repo (DatasetRepositoryProtocol):
                Repository instance satisfying the persistence contract.
            query_adapter (QueryAdapterProtocol):
                Adapter instance executing analytical SQL statements.
            planner_tool (ChartPlannerTool):
                Planner tool used for natural language chart inference.
        """
        self._dataset_repo = dataset_repo
        self._query_adapter = query_adapter
        self._planner_tool = planner_tool

    async def generate_chart(
        self,
        payload: AnalysisChartRequestDTO,
    ) -> AnalysisChartResponseDTO:
        """
        Generates chart specifications and execution data for a given dataset.

        Validates the dataset preparation status, processes either an explicit
        SQL statement or a natural language question, validates axis mapping,
        and builds the complete chart response DTO.

        Args:
            payload (AnalysisChartRequestDTO):
                Chart generation request parameters.

        Returns:
            AnalysisChartResponseDTO:
                Structured response with operation status, message, and chart data.

        Raises:
            ValueError:
                If SQL fails safe validation checks or axis fields are missing.
        """
        dataset = await self._dataset_repo.find_by_id(payload.dataset_id)
        if not dataset:
            return AnalysisChartResponseDTO(
                success=False,
                message=f"Dataset {payload.dataset_id} not found.",
                data=None,
            )

        status_value = getattr(dataset, "status", None)
        if status_value != DatasetStatus.PREPARED:
            return AnalysisChartResponseDTO(
                success=False,
                message=f"Dataset is not prepared. Current status: {status_value}",
                data=None,
            )

        table_name = getattr(dataset, "table_name", "dataset_table")
        available_columns = getattr(dataset, "columns", [])

        if payload.sql:
            validate_safe_select_query(payload.sql)
            target_sql = payload.sql
            target_type = payload.chart_type or ChartType.BAR
            target_x = payload.x_field
            target_y = payload.y_field
            title = f"Chart for dataset {payload.dataset_id}"
        elif payload.question:
            plan = self._planner_tool.plan(
                question=payload.question,
                table_name=table_name,
                available_columns=available_columns,
                limit=payload.limit,
            )
            target_sql = plan.sql
            target_type = plan.chart_type
            target_x = plan.x_field
            target_y = plan.y_field
            title = plan.title
        else:
            return AnalysisChartResponseDTO(
                success=False,
                message="Either 'sql' or 'question' must be provided.",
                data=None,
            )

        query_result = await self._query_adapter.execute_query(target_sql)
        columns = query_result.columns
        rows = query_result.rows

        resolved_x = target_x or (columns[0] if columns else "x")
        resolved_y = target_y or (columns[1] if len(columns) > 1 else resolved_x)

        if resolved_x not in columns:
            return AnalysisChartResponseDTO(
                success=False,
                message=f"Chart x_field '{resolved_x}' was not found in query results.",
                data=None,
            )
        if resolved_y not in columns:
            return AnalysisChartResponseDTO(
                success=False,
                message=f"Chart y_field '{resolved_y}' was not found in query results.",
                data=None,
            )

        chart_spec = ChartSpecBuilder.build(
            chart_type=target_type,
            title=title,
            x_field=resolved_x,
            y_field=resolved_y,
            columns=columns,
            rows=rows,
        )

        return AnalysisChartResponseDTO(
            success=True,
            message="Chart generated successfully.",
            data=AnalysisChartDataDTO(
                dataset_id=payload.dataset_id,
                chart_type=target_type,
                title=title,
                executed_sql=target_sql,
                x_field=resolved_x,
                y_field=resolved_y,
                columns=columns,
                rows=rows,
                chart_spec=chart_spec,
            ),
        )