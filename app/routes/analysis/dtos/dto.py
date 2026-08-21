from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
from app.enums.chart_type import ChartType


class AnalysisChartRequestDTO(BaseModel):
    """
    Data transfer object representing a request to generate a chart.

    Accepts either an explicit visualization specification (SQL query, chart
    type, and axis field mappings) or a natural-language question that will be
    interpreted and converted into a chart execution plan.

    Attributes:
        dataset_id:
            Unique identifier of the target dataset.
        question:
            Natural-language question used to infer the chart execution plan.
        sql:
            Explicit read-only SELECT analytical query.
        chart_type:
            Supported chart visualization type (bar, line, pie, table).
        x_field:
            Name of the column mapped to the horizontal axis or category.
        y_field:
            Name of the column mapped to the vertical axis or metric.
        limit:
            Maximum number of records to return from the analytical execution.
    """

    dataset_id: str
    question: Optional[str] = None
    sql: Optional[str] = None
    chart_type: Optional[ChartType] = None
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    limit: Optional[int] = Field(default=100, ge=1, le=1000)

    @model_validator(mode="after")
    def validate_inputs(self) -> "AnalysisChartRequestDTO":
        """
        Validates whether sufficient input parameters were provided.

        Ensures that the client supplied either a valid non-empty natural-language
        question or a complete explicit chart definition comprising SQL, chart
        type, x_field, and y_field.

        Returns:
            AnalysisChartRequestDTO:
                The validated request DTO instance.

        Raises:
            ValueError:
                If neither a question nor the complete set of explicit chart
                parameters is provided.
        """
        has_explicit = bool(
            self.sql and self.chart_type and self.x_field and self.y_field
        )
        has_question = bool(self.question and self.question.strip())

        if not (has_explicit or has_question):
            raise ValueError(
                "Either provide a 'question' or explicit chart parameters "
                "('sql', 'chart_type', 'x_field', 'y_field')."
            )
        return self


class ChartSpec(BaseModel):
    """
    Structured frontend-friendly chart specification.

    Attributes:
        type:
            Type of visual representation (e.g., bar, line, pie, table).
        title:
            Descriptive title for the chart visualization.
        x_field:
            Dimension or category field mapped to the X axis.
        y_field:
            Metric or numeric field mapped to the Y axis.
        series:
            List of series names present in the chart data.
        data:
            List of structured data points containing the mapped values.
    """

    type: str
    title: str
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    series: list[str] = []
    data: list[dict[str, Any]] = []


class AnalysisChartDataDTO(BaseModel):
    """
    Structured analytical payload returned upon successful chart generation.

    Attributes:
        dataset_id:
            Identifier of the analyzed dataset.
        chart_type:
            Resolved chart visualization type.
        title:
            Resolved title of the chart.
        executed_sql:
            Analytical SQL statement executed against the dataset.
        x_field:
            Field mapped to the X axis or category dimension.
        y_field:
            Field mapped to the Y axis or metric dimension.
        columns:
            List of column names returned by the executed query.
        rows:
            Raw row records retrieved during execution.
        chart_spec:
            Frontend-ready structured chart configuration and data.
    """

    dataset_id: str
    chart_type: str
    title: str
    executed_sql: str
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    columns: list[str]
    rows: list[dict[str, Any]]
    chart_spec: ChartSpec


class AnalysisChartResponseDTO(BaseModel):
    """
    Standardized API response DTO for dataset chart operations.

    Attributes:
        success:
            Indicates whether the chart generation operation succeeded.
        message:
            Descriptive message summarizing the operation outcome or error.
        data:
            Generated chart and query payload when the operation succeeds.
    """

    success: bool
    message: str
    data: Optional[AnalysisChartDataDTO] = None
