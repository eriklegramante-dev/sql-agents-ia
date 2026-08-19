import re
from typing import Any, Dict, List, Optional
from app.enums.chart_type import ChartType
from app.routes.analysis.dtos.dto import AnalysisChartDataDTO, AnalysisChartRequestDTO
from app.routes.analysis.helpers.chart_builder import ChartSpecBuilder
from app.routes.analysis.helpers.chart_planner import ChartPlannerTool
from app.security.sql_validator import validate_read_only_select


class AnalysisService:
    def __init__(
        self,
        dataset_repo: Any,
        query_adapter: Any,
        planner_tool: Optional[ChartPlannerTool] = None,
    ):
        self.dataset_repo = dataset_repo
        self.query_adapter = query_adapter
        self.planner_tool = planner_tool or ChartPlannerTool()

    def generate_chart(self, request: AnalysisChartRequestDTO) -> AnalysisChartDataDTO:
        dataset = self.dataset_repo.get_by_id(request.dataset_id)
        if not dataset:
            raise ValueError(f"Dataset '{request.dataset_id}' not found.")

        status = getattr(dataset, "status", None) or (dataset.get("status") if isinstance(dataset, dict) else None)
        if status not in ["prepared", "profiled"]:
            raise ValueError(f"Dataset '{request.dataset_id}' must be prepared or profiled before chart generation.")

        table_name = (
            getattr(dataset, "table_name", None)
            or (dataset.get("table_name") if isinstance(dataset, dict) else None)
            or f"dataset_{request.dataset_id}"
        )
        schema_cols = (
            getattr(dataset, "columns", None)
            or (dataset.get("columns") if isinstance(dataset, dict) else None)
            or []
        )

        if request.sql:
            sql = request.sql
            chart_type = request.chart_type.value if isinstance(request.chart_type, ChartType) else str(request.chart_type or "table")
            x_field = request.x_field
            y_field = request.y_field
            title = f"Analysis for {request.dataset_id}"
        else:
            plan = self.planner_tool.plan_chart(request.question or "", table_name, schema_cols)
            sql = plan.sql
            chart_type = plan.chart_type
            x_field = plan.x_field
            y_field = plan.y_field
            title = plan.title

        validate_read_only_select(sql)

        safe_limit = request.limit or 100
        if not re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE):
            sql = f"{sql.rstrip(';')} LIMIT {safe_limit}"

        query_result: Dict[str, Any] = self.query_adapter.execute_query(sql)
        columns: List[str] = query_result.get("columns", [])
        rows: List[Dict[str, Any]] = query_result.get("rows", [])

        if x_field and x_field not in columns:
            raise ValueError(f"Chart x_field '{x_field}' was not found in query results.")
        if y_field and y_field not in columns:
            raise ValueError(f"Chart y_field '{y_field}' was not found in query results.")

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