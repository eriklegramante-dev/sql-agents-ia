from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.adapters.analysis.duckdb_query_adapter import (
    DuckDBQueryResult,
)
from app.analysis.sql_safety_validator import SQLSafetyValidator
from app.core.analysis.workflow import AnalysisQueryWorkflow
from app.enums.dataset_status import DatasetStatus
from app.prepare.exceptions import AppException
from app.core.analysis.models import AnalysisQueryInput


class TestAnalysisQueryWorkflow:
    def setup_method(self) -> None:
        self.dataset_id = uuid4()

        self.dataset_repository = Mock()
        self.dataset_repository.get_by_id = AsyncMock()

        self.storage_adapter = Mock()
        self.storage_adapter.read_file = AsyncMock(return_value=b"parquet-content")

        self.sql_validator = SQLSafetyValidator()

        self.query_adapter = Mock()

        self.logger = Mock()

        self.workflow = AnalysisQueryWorkflow(
            dataset_repository=self.dataset_repository,
            storage_adapter=self.storage_adapter,
            sql_validator=self.sql_validator,
            query_adapter=self.query_adapter,
            logger=self.logger(),
        )

    def _build_dataset(
        self,
        status: DatasetStatus | str = DatasetStatus.PREPARED,
        prepared_object_key: str | None = "datasets/prepared.parquet",
        rows_count: int | None = 10,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            id=self.dataset_id,
            status=status,
            prepared_object_key=prepared_object_key,
            rows_count=rows_count,
        )

    @pytest.mark.anyio
    async def test_execute_should_return_analysis_result(self) -> None:
        dataset = self._build_dataset()

        self.dataset_repository.get_by_id.return_value = dataset

        self.query_adapter.execute.return_value = DuckDBQueryResult(
            columns=["id", "name"],
            rows=[
                {
                    "id": 1,
                    "name": "Alice",
                },
                {
                    "id": 2,
                    "name": "Bob",
                },
            ],
            rows_count=10,
            returned_rows_count=2,
        )

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            sql="SELECT id, name FROM dataset",
            limit=2,
        )

        result = await self.workflow.execute(request)

        assert result.dataset_id == self.dataset_id
        assert result.executed_sql == "SELECT id, name FROM dataset"
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
        ]
        assert result.rows_count == 10
        assert result.returned_rows_count == 2
        assert result.limit == 2

        self.dataset_repository.get_by_id.assert_awaited_once_with(self.dataset_id)

        self.storage_adapter.read_file.assert_awaited_once_with(
            container="prepared",
            path="datasets/prepared.parquet",
        )

        self.query_adapter.execute.assert_called_once_with(
            parquet_content=b"parquet-content",
            sql="SELECT id, name FROM dataset",
            limit=2,
        )

    @pytest.mark.anyio
    async def test_execute_should_raise_not_found_for_invalid_dataset(
        self,
    ) -> None:
        self.dataset_repository.get_by_id.return_value = None

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            sql="SELECT * FROM dataset",
        )

        with pytest.raises(AppException) as error:
            await self.workflow.execute(request)

        assert error.value.status_code == 404
        assert error.value.message == (f"Dataset {self.dataset_id} was not found.")

        self.storage_adapter.read_file.assert_not_awaited()
        self.query_adapter.execute.assert_not_called()

    @pytest.mark.anyio
    async def test_execute_should_reject_unprepared_dataset(
        self,
    ) -> None:
        dataset = self._build_dataset(
            status="UPLOADED",
        )

        self.dataset_repository.get_by_id.return_value = dataset

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            sql="SELECT * FROM dataset",
        )

        with pytest.raises(AppException) as error:
            await self.workflow.execute(request)

        assert error.value.status_code == 409
        assert error.value.message == (
            "Dataset must be prepared or profiled before analysis."
        )

        self.storage_adapter.read_file.assert_not_awaited()
        self.query_adapter.execute.assert_not_called()

    @pytest.mark.anyio
    async def test_execute_should_reject_dataset_without_prepared_object(
        self,
    ) -> None:
        dataset = self._build_dataset(
            prepared_object_key=None,
        )

        self.dataset_repository.get_by_id.return_value = dataset

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            sql="SELECT * FROM dataset",
        )

        with pytest.raises(AppException) as error:
            await self.workflow.execute(request)

        assert error.value.status_code == 409
        assert error.value.message == (
            "Dataset does not have a prepared object available."
        )

        self.storage_adapter.read_file.assert_not_awaited()
        self.query_adapter.execute.assert_not_called()

    @pytest.mark.anyio
    async def test_execute_should_reject_unsafe_sql(self) -> None:
        dataset = self._build_dataset()

        self.dataset_repository.get_by_id.return_value = dataset

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            sql="DELETE FROM dataset",
        )

        with pytest.raises(AppException) as error:
            await self.workflow.execute(request)

        assert error.value.status_code == 422
        assert error.value.message == ("Only SELECT statements are allowed.")

        self.query_adapter.execute.assert_not_called()

    @pytest.mark.anyio
    async def test_execute_should_reject_question_without_sql(
        self,
    ) -> None:
        dataset = self._build_dataset()

        self.dataset_repository.get_by_id.return_value = dataset

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            question="What is the average score?",
        )

        with pytest.raises(AppException) as error:
            await self.workflow.execute(request)

        assert error.value.status_code == 422
        assert error.value.message == (
            "Natural-language query generation is not available yet. "
            "Provide a direct SQL query for analysis."
        )

        self.query_adapter.execute.assert_not_called()

    @pytest.mark.anyio
    async def test_execute_should_prioritize_sql_over_question(
        self,
    ) -> None:
        dataset = self._build_dataset()

        self.dataset_repository.get_by_id.return_value = dataset

        self.query_adapter.execute.return_value = DuckDBQueryResult(
            columns=["total"],
            rows=[
                {
                    "total": 10,
                }
            ],
            rows_count=1,
            returned_rows_count=1,
        )

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            question="How many rows are there?",
            sql="SELECT COUNT(*) AS total FROM dataset",
            limit=20,
        )

        result = await self.workflow.execute(request)

        assert result.executed_sql == ("SELECT COUNT(*) AS total FROM dataset")

        self.query_adapter.execute.assert_called_once_with(
            parquet_content=b"parquet-content",
            sql="SELECT COUNT(*) AS total FROM dataset",
            limit=20,
        )

    @pytest.mark.anyio
    async def test_execute_should_remove_sql_trailing_semicolon(
        self,
    ) -> None:
        dataset = self._build_dataset()

        self.dataset_repository.get_by_id.return_value = dataset

        self.query_adapter.execute.return_value = DuckDBQueryResult(
            columns=["id"],
            rows=[
                {
                    "id": 1,
                }
            ],
            rows_count=1,
            returned_rows_count=1,
        )

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            sql="SELECT id FROM dataset;",
        )

        result = await self.workflow.execute(request)

        assert result.executed_sql == "SELECT id FROM dataset"

        self.query_adapter.execute.assert_called_once_with(
            parquet_content=b"parquet-content",
            sql="SELECT id FROM dataset",
            limit=20,
        )

    @pytest.mark.anyio
    async def test_execute_should_use_default_limit(self) -> None:
        dataset = self._build_dataset()

        self.dataset_repository.get_by_id.return_value = dataset

        self.query_adapter.execute.return_value = DuckDBQueryResult(
            columns=["id"],
            rows=[],
            rows_count=0,
            returned_rows_count=0,
        )

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            sql="SELECT id FROM dataset",
        )

        result = await self.workflow.execute(request)

        assert result.limit == 20

        self.query_adapter.execute.assert_called_once_with(
            parquet_content=b"parquet-content",
            sql="SELECT id FROM dataset",
            limit=20,
        )
