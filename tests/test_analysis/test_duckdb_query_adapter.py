from datetime import date
from decimal import Decimal
from io import BytesIO

import pandas as pd
import pytest

from app.adapters.analysis.duckdb_query_adapter import (
    DuckDBQueryAdapter,
)


class TestDuckDBQueryAdapter:
    def setup_method(self) -> None:
        self.adapter = DuckDBQueryAdapter()

    def _build_parquet_content(self) -> bytes:
        dataframe = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "score": [Decimal("10.50"), Decimal("20.75"), Decimal("30.00")],
                "created_at": [
                    date(2026, 1, 1),
                    date(2026, 1, 2),
                    date(2026, 1, 3),
                ],
            }
        )

        buffer = BytesIO()

        dataframe.to_parquet(
            buffer,
            index=False,
        )

        return buffer.getvalue()

    def test_execute_should_return_query_result(self) -> None:
        parquet_content = self._build_parquet_content()

        result = self.adapter.execute(
            parquet_content=parquet_content,
            sql="SELECT id, name FROM dataset ORDER BY id",
            limit=10,
        )

        assert result.columns == ["id", "name"]
        assert result.rows == [
            {
                "id": 1,
                "name": "Alice",
            },
            {
                "id": 2,
                "name": "Bob",
            },
            {
                "id": 3,
                "name": "Charlie",
            },
        ]
        assert result.rows_count == 3
        assert result.returned_rows_count == 3

    def test_execute_should_enforce_row_limit(self) -> None:
        parquet_content = self._build_parquet_content()

        result = self.adapter.execute(
            parquet_content=parquet_content,
            sql="SELECT id, name FROM dataset ORDER BY id",
            limit=2,
        )

        assert result.rows_count == 3
        assert result.returned_rows_count == 2
        assert len(result.rows) == 2
        assert result.rows == [
            {
                "id": 1,
                "name": "Alice",
            },
            {
                "id": 2,
                "name": "Bob",
            },
        ]

    def test_execute_should_serialize_values_to_json_safe_format(
        self,
    ) -> None:
        parquet_content = self._build_parquet_content()

        result = self.adapter.execute(
            parquet_content=parquet_content,
            sql=("SELECT score, created_at " "FROM dataset " "WHERE id = 1"),
            limit=10,
        )

        assert result.rows_count == 1
        assert result.returned_rows_count == 1
        assert result.rows == [
            {
                "score": 10.5,
                "created_at": "2026-01-01",
            }
        ]

    def test_execute_should_reject_empty_parquet_content(self) -> None:
        with pytest.raises(
            ValueError,
            match="Parquet content must not be empty.",
        ):
            self.adapter.execute(
                parquet_content=b"",
                sql="SELECT * FROM dataset",
                limit=10,
            )

    def test_execute_should_reject_empty_sql(self) -> None:
        parquet_content = self._build_parquet_content()

        with pytest.raises(
            ValueError,
            match="SQL query must not be empty.",
        ):
            self.adapter.execute(
                parquet_content=parquet_content,
                sql="   ",
                limit=10,
            )

    def test_execute_should_reject_invalid_limit(self) -> None:
        parquet_content = self._build_parquet_content()

        with pytest.raises(
            ValueError,
            match="Query limit must be greater than zero.",
        ):
            self.adapter.execute(
                parquet_content=parquet_content,
                sql="SELECT * FROM dataset",
                limit=0,
            )

    def test_execute_should_raise_runtime_error_for_invalid_query(
        self,
    ) -> None:
        parquet_content = self._build_parquet_content()

        with pytest.raises(
            RuntimeError,
            match="Unable to execute the analytical query.",
        ):
            self.adapter.execute(
                parquet_content=parquet_content,
                sql="SELECT unknown_column FROM dataset",
                limit=10,
            )
