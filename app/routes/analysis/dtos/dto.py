"""
Data transfer objects representing chart requests, analytical queries, and responses.

Defines validation boundaries and payload contracts for dataset analysis endpoints.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums.chart_type import ChartType


class AnalysisQueryRequestDTO(BaseModel):
    """
    Represents an incoming dataset analysis query request.

    The request allows the client to submit either a natural-language
    question, a direct SQL query, or both. When both values are provided,
    the analysis workflow must prioritize the direct SQL query.

    At least one of ``question`` or ``sql`` must be provided.
    """

    model_config = ConfigDict(extra="forbid")

    dataset_id: UUID = Field(
        ...,
        description="Unique identifier of the dataset to be analyzed.",
    )
    question: str | None = Field(
        default=None,
        description=(
            "Optional natural-language analytical question to execute "
            "against the dataset."
        ),
    )
    sql: str | None = Field(
        default=None,
        description=(
            "Optional direct read-only SQL query to execute against " "the dataset."
        ),
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of rows returned by the analysis query.",
    )

    @field_validator("question", "sql", mode="before")
    @classmethod
    def normalize_optional_query_value(
        cls,
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError("Query values must be strings.")

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value

    @field_validator("limit", mode="before")
    @classmethod
    def normalize_limit(
        cls,
        value: Any,
    ) -> int:
        if value is None or value == "":
            return 20
        return int(value)

    @model_validator(mode="after")
    def validate_query_input(self) -> "AnalysisQueryRequestDTO":
        if self.question is None and self.sql is None:
            raise ValueError("At least one of 'question' or 'sql' must be provided.")
        return self


class AnalysisQueryResponseDataDTO(BaseModel):
    """
    Represents the dataset analysis query result.
    """

    dataset_id: UUID
    executed_sql: str
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    rows_count: int
    returned_rows_count: int
    limit: int


class AnalysisQueryResponseDTO(BaseModel):
    """
    Represents the standardized API response for dataset analysis queries.
    """

    success: bool
    message: str
    data: AnalysisQueryResponseDataDTO | None = None
    errors: list[Any] | None = None


class AnalysisChartRequestDTO(BaseModel):
    """
    Data transfer object representing a request to generate a chart.

    Accepts either an explicit visualization specification (SQL query, chart
    type, and axis field mappings) or a natural-language question that will be
    interpreted and converted into a chart execution plan.
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
    """

    success: bool
    message: str
    data: AnalysisChartDataDTO | None = None
