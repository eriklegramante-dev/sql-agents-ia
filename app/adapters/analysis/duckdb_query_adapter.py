import math
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import UUID

import duckdb


@dataclass(frozen=True)
class DuckDBQueryResult:
    """
    Represents the result of an analytical DuckDB query.

    Attributes:
        columns:
            Ordered column names returned by the executed query.

        rows:
            JSON-safe rows returned after applying the requested limit.

        rows_count:
            Total number of rows produced by the analytical query before
            applying the response limit.

        returned_rows_count:
            Number of rows included in the returned result.
    """

    columns: list[str]
    rows: list[dict[str, Any]]
    rows_count: int
    returned_rows_count: int


class DuckDBQueryAdapter:
    """
    Executes read-only analytical queries against Parquet datasets.

    This adapter receives prepared Parquet content and an already validated
    SQL query, exposes the Parquet data as a temporary ``dataset`` view, and
    executes the query using an isolated in-memory DuckDB connection.

    The adapter enforces the response row limit independently from the SQL
    provided by the client. It also converts returned values into JSON-safe
    representations before returning them to the workflow.

    SQL safety validation is intentionally not performed in this class.
    Queries must be validated before reaching the adapter.

    The adapter does not persist data and does not modify the source Parquet
    object.
    """

    DATASET_VIEW_NAME: str = "dataset"

    def execute(
        self,
        parquet_content: bytes,
        sql: str,
        limit: int,
    ) -> DuckDBQueryResult:
        """
        Execute an analytical query against prepared Parquet content.

        Args:
            parquet_content:
                Binary content of the prepared Parquet dataset.

            sql:
                Validated read-only SQL query to execute.

            limit:
                Maximum number of rows to include in the returned result.

        Returns:
            DuckDBQueryResult:
                Structured analytical result containing columns, JSON-safe
                rows, total query row count, and returned row count.

        Raises:
            ValueError:
                If the Parquet content is empty, SQL is empty, or the row
                limit is invalid.

            RuntimeError:
                If DuckDB cannot execute the analytical query.
        """
        self._validate_inputs(
            parquet_content=parquet_content,
            sql=sql,
            limit=limit,
        )

        temporary_path: Path | None = None

        try:
            temporary_path = self._write_temporary_parquet(
                parquet_content,
            )

            return self._execute_query(
                parquet_path=temporary_path,
                sql=sql,
                limit=limit,
            )

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def _execute_query(
        self,
        parquet_path: Path,
        sql: str,
        limit: int,
    ) -> DuckDBQueryResult:
        """
        Execute SQL using an isolated DuckDB connection.

        Args:
            parquet_path:
                Temporary path containing the prepared Parquet content.

            sql:
                Validated analytical SQL query.

            limit:
                Maximum number of rows returned to the caller.

        Returns:
            DuckDBQueryResult:
                Structured query execution result.

        Raises:
            RuntimeError:
                If DuckDB cannot execute the query.
        """
        connection = duckdb.connect(database=":memory:")

        try:
            connection.read_parquet(
                str(parquet_path),
            ).create_view(
                self.DATASET_VIEW_NAME,
            )

            rows_count = self._count_query_rows(
                connection=connection,
                sql=sql,
            )

            limited_sql = f"SELECT * FROM ({sql}) AS analysis_result " f"LIMIT {limit}"

            cursor = connection.execute(limited_sql)

            columns = [description[0] for description in cursor.description]

            raw_rows = cursor.fetchall()

            rows = [
                {
                    column: self._to_json_safe(value)
                    for column, value in zip(columns, row, strict=True)
                }
                for row in raw_rows
            ]

            return DuckDBQueryResult(
                columns=columns,
                rows=rows,
                rows_count=rows_count,
                returned_rows_count=len(rows),
            )

        except duckdb.Error as error:
            raise RuntimeError("Unable to execute the analytical query.") from error

        finally:
            connection.close()

    def _count_query_rows(
        self,
        connection: duckdb.DuckDBPyConnection,
        sql: str,
    ) -> int:
        """
        Count the total rows produced by the analytical query.

        The original query is wrapped as a subquery so the count represents
        the complete analytical result before the response limit is applied.

        Args:
            connection:
                Active DuckDB connection.

            sql:
                Validated analytical SQL query.

        Returns:
            int:
                Total number of rows produced by the query.
        """
        count_sql = f"SELECT COUNT(*) FROM ({sql}) AS analysis_count"

        result = connection.execute(count_sql).fetchone()

        if result is None:
            return 0

        return int(result[0])

    def _write_temporary_parquet(
        self,
        parquet_content: bytes,
    ) -> Path:
        """
        Write Parquet content to a temporary file.

        DuckDB can efficiently scan Parquet files directly. The temporary
        file exists only for the duration of the analytical query and is
        removed after execution.

        Args:
            parquet_content:
                Binary prepared Parquet content.

        Returns:
            Path:
                Path to the temporary Parquet file.
        """
        with NamedTemporaryFile(
            suffix=".parquet",
            delete=False,
        ) as temporary_file:
            temporary_file.write(parquet_content)

            return Path(temporary_file.name)

    def _validate_inputs(
        self,
        parquet_content: bytes,
        sql: str,
        limit: int,
    ) -> None:
        """
        Validate adapter execution inputs.

        Args:
            parquet_content:
                Binary prepared Parquet content.

            sql:
                Validated analytical SQL query.

            limit:
                Maximum number of rows to return.

        Raises:
            ValueError:
                If any required execution input is invalid.
        """
        if not parquet_content:
            raise ValueError("Parquet content must not be empty.")

        if not sql.strip():
            raise ValueError("SQL query must not be empty.")

        if limit <= 0:
            raise ValueError("Query limit must be greater than zero.")

    def _to_json_safe(
        self,
        value: Any,
    ) -> Any:
        """
        Convert a DuckDB result value into a JSON-safe representation.

        Args:
            value:
                Value returned by DuckDB.

        Returns:
            Any:
                JSON-safe representation of the provided value.
        """
        if value is None:
            return None

        if isinstance(value, (datetime, date, time)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, UUID):
            return str(value)

        if isinstance(value, bytes):
            return value.hex()

        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None

            return value

        if isinstance(value, list):
            return [self._to_json_safe(item) for item in value]

        if isinstance(value, tuple):
            return [self._to_json_safe(item) for item in value]

        if isinstance(value, dict):
            return {str(key): self._to_json_safe(item) for key, item in value.items()}

        return value
