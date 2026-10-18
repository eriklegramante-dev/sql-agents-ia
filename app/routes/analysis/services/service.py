"""
Analysis service implementation.

Orchestrates chart planning, analytical query generation, SQL security
validation, and chart specification construction, as well as delegating
data queries to the analysis workflow.
"""

from app.enums.chart_type import ChartType
from app.enums.dataset_status import DatasetStatus
from app.routes.analysis.helpers.chart_builder import ChartSpecBuilder
from app.routes.analysis.helpers.chart_planner import ChartPlannerTool
from app.routes.analysis.protocols import (
    DatasetRepositoryProtocol,
    QueryAdapterProtocol,
)
from app.security.sql_validator import validate_safe_select_query
from app.routes.analysis.dtos.dto import (
    AnalysisChartDataDTO,
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
    AnalysisQueryRequestDTO,
    AnalysisQueryResponseDataDTO,
)

from app.core.analysis.workflow import AnalysisQueryWorkflow
from app.logs.setup_logger import LOGGER, LoggerManager
from app.core.analysis.models import AnalysisQueryInput


class AnalysisQueryService:
    """
    Coordinates dataset analysis query execution at the service layer.
    Maps HTTP DTOs to core input and forwards the trusted caller identity.
    """

    def __init__(
        self,
        workflow: AnalysisQueryWorkflow,
        logger: LoggerManager,
    ) -> None:
        self.workflow = workflow
        self.logger = logger

    async def execute(
        self,
        request: AnalysisQueryRequestDTO,
        *,
        user_id: int,
    ) -> AnalysisQueryResponseDataDTO:
        """Map the analysis request to core input and return response data.

        Args:
            request: Validated query request received from the controller.
            user_id: Trusted route identity forwarded for dataset ownership checks.

        Returns:
            Response data after query execution and success recording complete.

        Workflow validation, storage, execution, and persistence failures
        propagate to the controller without building a successful response.
        """
        self.logger.log_info(
            f"Executing analysis query service for dataset " f"{request.dataset_id}."
        )

        workflow_request = AnalysisQueryInput(
            dataset_id=request.dataset_id,
            question=request.question,
            sql=request.sql,
            limit=request.limit,
        )

        result = await self.workflow.execute(workflow_request, user_id=user_id)

        response_data = AnalysisQueryResponseDataDTO(
            dataset_id=result.dataset_id,
            executed_sql=result.executed_sql,
            columns=result.columns,
            rows=result.rows,
            rows_count=result.rows_count,
            returned_rows_count=result.returned_rows_count,
            limit=result.limit,
        )

        self.logger.log_info(
            f"Analysis query service completed for dataset " f"{request.dataset_id}."
        )

        return response_data


class AnalysisService:
    """
    Application service managing analytical chart generation.
    """

    def __init__(
        self,
        dataset_repo: DatasetRepositoryProtocol,
        query_adapter: QueryAdapterProtocol,
        planner_tool: ChartPlannerTool,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._query_adapter = query_adapter
        self._planner_tool = planner_tool

    async def generate_chart(
        self,
        payload: AnalysisChartRequestDTO,
    ) -> AnalysisChartResponseDTO:
        dataset = await self._dataset_repo.find_by_id(payload.dataset_id)
        if not dataset:
            return AnalysisChartResponseDTO(
                success=False,
                message=f"Dataset {payload.dataset_id} not found.",
                data=None,
            )

        if dataset.status != DatasetStatus.PREPARED:
            return AnalysisChartResponseDTO(
                success=False,
                message=f"Dataset is not prepared. Current status: {dataset.status}",
                data=None,
            )

        table_name = dataset.table_name
        available_columns = dataset.columns

        if payload.sql:
            validate_safe_select_query(payload.sql)
            target_sql = payload.sql
            target_type = payload.chart_type or ChartType.BAR
            target_x = payload.x_field
            target_y = payload.y_field
            title = f"Chart for dataset {payload.dataset_id}"
        elif payload.question:
            plan = self._planner_tool.plan_chart(
                question=payload.question,
                table_name=table_name,
                schema_columns=available_columns,
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
            rows=rows,
        )

        return AnalysisChartResponseDTO(
            success=True,
            message="Chart generated successfully.",
            data=AnalysisChartDataDTO(
                dataset_id=payload.dataset_id,
                chart_type=(
                    target_type.value
                    if hasattr(target_type, "value")
                    else str(target_type)
                ),
                title=title,
                executed_sql=target_sql,
                x_field=resolved_x,
                y_field=resolved_y,
                columns=columns,
                rows=rows,
                chart_spec=chart_spec,
            ),
        )
