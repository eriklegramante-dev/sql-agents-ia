from typing import Any, Protocol
from uuid import UUID


class AnalysisDataset(Protocol):
    """
    Defines the dataset metadata required by the analysis workflow.

    Attributes:
        user_id:
            Dataset owner identifier, or None for unassigned datasets.

        status:
            Current dataset processing status.

        prepared_object_key:
            Storage object key of the prepared Parquet dataset.
    """

    user_id: int | None
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


class QueryExecutionRecorder(Protocol):
    """Define the persistence contract for completed analytical queries.

    The calling workflow checks ownership and executes the query before
    requesting a success record. Implementations report persistence failures
    to the caller rather than suppressing them.
    """

    async def record_success(
        self,
        *,
        user_id: int,
        dataset_id: UUID,
    ) -> None:
        """Persist a record after an analytical query has completed.

        Args:
            user_id: Trusted caller identity already checked against the owner.
            dataset_id: Identifier of the dataset used by the query.

        Returns:
            None after persistence completes.

        Persistence failures must propagate rather than signal success.
        """
        ...


class QueryExecutionCounter(Protocol):
    """Define retrieval of persisted query execution counts by user.

    The caller supplies the trusted user identifier. Implementations scope
    the count to that identifier and distinguish an empty history from a
    persistence failure.
    """

    async def count_by_user(self, *, user_id: int) -> int:
        """Count persisted successful executions for the supplied user.

        Args:
            user_id: Trusted user identifier used to scope the count.

        Returns:
            Number of persisted executions, including zero when none exist.

        Repository failures must propagate rather than return a zero count.
        """
        ...