from typing import Any, Protocol
from uuid import UUID


class AnalysisDataset(Protocol):
    """
    Defines the dataset metadata required by the analysis workflow.

    Attributes:
        status:
            Current dataset processing status.

        prepared_object_key:
            Storage object key of the prepared Parquet dataset.
    """

    status: str
    prepared_object_key: str | None


class AnalysisDatasetRepository(Protocol):
    """
    Defines the dataset repository contract required by the analysis workflow.
    """

    async def get_by_id(
        self,
        dataset_id: UUID,
    ) -> AnalysisDataset | None:
        """
        Retrieve dataset metadata by its unique identifier.

        Args:
            dataset_id:
                Unique identifier of the dataset.

        Returns:
            AnalysisDataset | None:
                Dataset metadata when found, otherwise None.
        """
        ...


class SQLValidator(Protocol):
    """
    Defines the SQL validation contract required by the analysis workflow.
    """

    def validate(
        self,
        sql: str,
    ) -> str:
        """
        Validate and normalize an analytical SQL query.

        Args:
            sql:
                SQL query to validate.

        Returns:
            str:
                Validated and normalized SQL query.
        """
        ...


class AnalysisQueryResult(Protocol):
    """
    Defines the analytical query result required by the analysis workflow.

    Attributes:
        columns:
            Ordered result column names.

        rows:
            Rows returned by the analytical query.

        rows_count:
            Total number of rows produced by the query.

        returned_rows_count:
            Number of rows returned to the caller.
    """

    columns: list[str]
    rows: list[dict[str, Any]]
    rows_count: int
    returned_rows_count: int


class AnalysisQueryExecutor(Protocol):
    """
    Defines the analytical query execution contract required by analysis.
    """

    def execute(
        self,
        parquet_content: bytes,
        sql: str,
        limit: int,
    ) -> AnalysisQueryResult:
        """
        Execute a validated analytical query.

        Args:
            parquet_content:
                Binary content of the prepared Parquet dataset.

            sql:
                Validated read-only SQL query.

            limit:
                Maximum number of rows to return.

        Returns:
            AnalysisQueryResult:
                Structured analytical query result.
        """
        ...
