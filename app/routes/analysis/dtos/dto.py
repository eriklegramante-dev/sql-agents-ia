"""
Data transfer objects representing chart requests and analytical responses.

Defines validation boundaries and payload contracts for dataset chart endpoints.
"""

from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.enums.chart_type import ChartType


class AnalysisChartRequestDTO(BaseModel):
    """
    Data transfer object representing a request to generate a chart.

    Accepts either an explicit visualization specification (SQL query, chart
    type, and axis field mappings) or a natural-language question that will be
    interpreted and converted into a chart execution plan.

    Attributes:
        dataset_id (UUID):
            Unique identifier of the target dataset.
        question (str | None):
            Natural-language question used to infer the chart execution plan.
        sql (str | None):
            Explicit read-only SELECT analytical query.
        chart_type (ChartType | None):
            Supported chart visualization type (bar, line, pie, table).
        x_field (str | None):
            Name of the column mapped to the horizontal axis or category.
        y_field (str | None):
            Name of the column mapped to the vertical axis or metric.
        limit (int):
            Maximum number of records to return from the analytical execution.
    """

    dataset_id: UUID
    question: str | None = None
    sql: str | None = None
    chart_type: ChartType | None = None
    x_field: str | None = None
    y_field: str | None = None
    limit: int = Field(default=50, ge=1, le=1000)

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
        type (str):
            Type of visual representation (e.g., bar, line, pie, table).
        title (str):
            Descriptive title for the chart visualization.
        x_field (str | None):
            Dimension or category field mapped to the X axis.
        y_field (str | None):
            Metric or numeric field mapped to the Y axis.
        series (list[str]):
            List of series names present in the chart data.
        data (list[dict[str, object]]):
            List of structured data points containing the mapped values.
    """

    type: str
    title: str
    x_field: str | None = None
    y_field: str | None = None
    series: list[str] = Field(default_factory=list)
    data: list[dict[str, object]] = Field(default_factory=list)


class AnalysisChartDataDTO(BaseModel):
    """
    Structured analytical payload returned upon successful chart generation.

    Attributes:
        dataset_id (UUID):
            Identifier of the analyzed dataset.
        chart_type (str):
            Resolved chart visualization type.
        title (str):
            Resolved title of the chart.
        executed_sql (str):
            Analytical SQL statement executed against the dataset.
        x_field (str | None):
            Field mapped to the X axis or category dimension.
        y_field (str | None):
            Field mapped to the Y axis or metric dimension.
        columns (list[str]):
            List of column names returned by the executed query.
        rows (list[dict[str, object]]):
            Raw row records retrieved during execution.
        chart_spec (ChartSpec):
            Frontend-ready structured chart configuration and data.
    """

    dataset_id: UUID
    chart_type: str
    title: str
    executed_sql: str
    x_field: str | None = None
    y_field: str | None = None
    columns: list[str]
    rows: list[dict[str, object]]
    chart_spec: ChartSpec


class AnalysisChartResponseDTO(BaseModel):
    """
    Standardized API response DTO for dataset chart operations.

    Attributes:
        success (bool):
            Indicates whether the chart generation operation succeeded.
        message (str):
            Descriptive message summarizing the operation outcome or error.
        data (AnalysisChartDataDTO | None):
            Generated chart and query payload when the operation succeeds.
    """

    success: bool
    message: str
    data: AnalysisChartDataDTO | None = None