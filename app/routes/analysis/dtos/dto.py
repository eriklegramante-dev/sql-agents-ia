from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AnalysisQueryRequestDTO(BaseModel):
    """
    Represents an incoming dataset analysis query request.

    The request allows the client to submit either a natural-language
    question, a direct SQL query, or both. When both values are provided,
    the analysis workflow must prioritize the direct SQL query.

    At least one of ``question`` or ``sql`` must be provided.

    Attributes:
        dataset_id:
            Unique identifier of the dataset to be analyzed.

        question:
            Optional natural-language analytical question that may be
            converted into SQL by the analysis workflow.

        sql:
            Optional direct SQL query to execute against the prepared
            dataset. Direct SQL takes priority when both SQL and a
            natural-language question are provided.

        limit:
            Maximum number of rows that may be returned by the analysis
            query.
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
            "Optional direct read-only SQL query to execute against "
            "the dataset."
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
        """
        Normalize optional question and SQL values.

        Empty strings and whitespace-only values are converted to ``None``.
        Valid string values are stripped of surrounding whitespace.

        Args:
            value:
                Raw question or SQL value received from the request payload.

        Returns:
            str | None:
                Normalized string value or ``None`` when the provided value
                is empty.

        Raises:
            ValueError:
                If a non-string value is provided.
        """
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
        """
        Normalize the optional row limit.

        When the client explicitly sends ``null`` or an empty value, the
        default safe limit is applied.

        Args:
            value:
                Raw limit value received from the request payload.

        Returns:
            int:
                Normalized row limit.
        """
        if value is None or value == "":
            return 20

        return int(value)

    @model_validator(mode="after")
    def validate_query_input(self) -> "AnalysisQueryRequestDTO":
        """
        Validate that the request contains an analytical query input.

        At least one of ``question`` or ``sql`` must be provided. The DTO
        accepts both simultaneously because SQL priority is a business rule
        handled by the analysis workflow.

        Returns:
            AnalysisQueryRequestDTO:
                Validated request instance.

        Raises:
            ValueError:
                If neither a natural-language question nor SQL query was
                provided.
        """
        if self.question is None and self.sql is None:
            raise ValueError(
                "At least one of 'question' or 'sql' must be provided."
            )

        return self


class AnalysisQueryResponseDataDTO(BaseModel):
    """
    Represents the dataset analysis query result.

    Attributes:
        dataset_id:
            Identifier of the analyzed dataset.

        executed_sql:
            Final SQL query executed against the prepared dataset.

        columns:
            Ordered list of column names returned by the query.

        rows:
            JSON-safe rows returned by the analytical query.

        rows_count:
            Total number of rows represented by the query result before the
            response limit is applied, when available.

        returned_rows_count:
            Number of rows included in the API response.

        limit:
            Safe row limit applied to the analytical query.
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

    Attributes:
        success:
            Indicates whether the analysis query completed successfully.

        message:
            Human-readable description of the operation result.

        data:
            Structured analytical query result when execution succeeds.

        errors:
            Optional list containing validation or execution error details.
    """

    success: bool
    message: str
    data: AnalysisQueryResponseDataDTO | None = None
    errors: list[Any] | None = None