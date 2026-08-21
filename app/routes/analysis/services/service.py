import re
from typing import Any, Optional
from uuid import UUID

from app.database.dataset_repository import DatasetRepository
from app.enums.chart_type import ChartType
from app.enums.dataset_status import DatasetStatus
from app.routes.analysis.dtos.dto import (
    AnalysisChartDataDTO,
    AnalysisChartRequestDTO,
)
from app.routes.analysis.helpers.chart_builder import ChartSpecBuilder
from app.routes.analysis.helpers.chart_planner import ChartPlannerTool
from app.security.sql_validator import validate_read_only_select


class AnalysisService:
    """
    Service responsible for orchestrating dataset chart generation workflows.

    Coordinates dataset state verification, chart planning from natural-language
    inputs or explicit parameters, analytical SQL validation, query execution,
    and structured chart specification assembly.

    Attributes:
        dataset_repo:
            Repository responsible for retrieving dataset persistence entities.
        query_adapter:
            Analytical query execution adapter used to run SQL statements.
        planner_tool:
            Tool responsible for converting natural-language prompts into
            executable chart plans.
    """

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        query_adapter: Any,
        planner_tool: Optional[ChartPlannerTool] = None,
    ) -> None:
        """
        Initialize the AnalysisService.

        Args:
            dataset_repo:
                Repository instance used to fetch dataset metadata and status.
            query_adapter:
                Adapter responsible for executing analytical SELECT queries.
            planner_tool:
                Optional helper tool for planning queries and chart types from
                natural-language questions. Defaults to ChartPlannerTool.
        """
        self.dataset_repo = dataset_repo
        self.query_adapter = query_adapter
        self.planner_tool = planner_tool or ChartPlannerTool()

    async def generate_chart(
        self,
        request: AnalysisChartRequestDTO,
    ) -> AnalysisChartDataDTO:
        """
        Executes the chart generation workflow for a target dataset.

        Validates that the dataset exists and is in a prepared or profiled state,
        resolves the analytical SQL query (via explicit parameters or natural-language
        planner), validates SQL safety rules, enforces execution row limits, executes
        the query through the query adapter, and builds the final chart specification.

        Args:
            request:
                Data transfer object containing the dataset identifier and chart
                generation parameters (explicit SQL/fields or a natural question).

        Returns:
            AnalysisChartDataDTO:
                Structured result containing chart properties, executed SQL,
                raw records, and the frontend-ready chart specification.

        Raises:
            ValueError:
                If the dataset does not exist, is not prepared/profiled, contains
                unsafe SQL, or refers to axis fields missing from query results.
        """
        dataset_uuid = UUID(request.dataset_id)
        dataset = await self.dataset_repo.find_by_id(dataset_uuid)

        if not dataset:
            raise ValueError(f"Dataset '{request.dataset_id}' not found.")

        if dataset.status not in (DatasetStatus.PREPARED, DatasetStatus.PROFILED):
            raise ValueError(
                f"Dataset '{request.dataset_id}' must be prepared or profiled "
                "before chart generation."
            )

        table_name = (
            getattr(dataset, "table_name", None)
            or f"dataset_{request.dataset_id.replace('-', '_')}"
        )
        schema_cols = getattr(dataset, "columns", None) or []

        if request.sql:
            sql = request.sql
            chart_type = (
                request.chart_type.value
                if isinstance(request.chart_type, ChartType)
                else str(request.chart_type or "table")
            )
            x_field = request.x_field
            y_field = request.y_field
            title = f"Analysis for {request.dataset_id}"
        else:
            plan = self.planner_tool.plan_chart(
                request.question or "",
                table_name,
                schema_cols,
            )
            sql = plan.sql
            chart_type = plan.chart_type
            x_field = plan.x_field
            y_field = plan.y_field
            title = plan.title

        validate_read_only_select(sql)

        safe_limit = request.limit or 100
        if not re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE):
            sql = f"{sql.rstrip(';')} LIMIT {safe_limit}"

        query_result: dict[str, Any] = await self.query_adapter.execute_query(sql)
        columns: list[str] = query_result.get("columns", [])
        rows: list[dict[str, Any]] = query_result.get("rows", [])

        if x_field and x_field not in columns:
            raise ValueError(
                f"Chart x_field '{x_field}' was not found in query results."
            )
        if y_field and y_field not in columns:
            raise ValueError(
                f"Chart y_field '{y_field}' was not found in query results."
            )

        chart_spec = ChartSpecBuilder.build(
            chart_type=chart_type,
            title=title,
            x_field=x_field,
            y_field=y_field,
            rows=rows,
        )

        return AnalysisChartDataDTO(
            dataset_id=request.dataset_id,
            chart_type=chart_type,
            title=title,
            executed_sql=sql,
            x_field=x_field,
            y_field=y_field,
            columns=columns,
            rows=rows,
            chart_spec=chart_spec,
        )
