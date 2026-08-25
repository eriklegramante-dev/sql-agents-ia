from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class AnalysisQueryInput:
    """
    Represents an analytical query request at the core boundary.

    Attributes:
        dataset_id:
            Identifier of the dataset to analyze.

        question:
            Optional natural-language analytical question.

        sql:
            Optional direct SQL query.

        limit:
            Optional maximum number of rows to return.
    """

    dataset_id: UUID
    question: str | None = None
    sql: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class AnalysisQueryOutput:
    """
    Represents the analytical result produced by the core workflow.

    Attributes:
        dataset_id:
            Identifier of the analyzed dataset.

        executed_sql:
            SQL query executed against the prepared dataset.

        columns:
            Ordered result column names.

        rows:
            JSON-safe rows returned by the query.

        rows_count:
            Total number of rows produced by the query.

        returned_rows_count:
            Number of rows returned to the caller.

        limit:
            Row limit applied during execution.
    """

    dataset_id: UUID
    executed_sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    rows_count: int
    returned_rows_count: int
    limit: int