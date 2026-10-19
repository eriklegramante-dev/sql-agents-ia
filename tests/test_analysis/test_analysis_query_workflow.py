from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call
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

        self.execution_repository = Mock(record_success=AsyncMock())
        self.workflow = AnalysisQueryWorkflow(
            dataset_repository=self.dataset_repository,
            storage_adapter=self.storage_adapter,
            sql_validator=self.sql_validator,
            query_adapter=self.query_adapter,
            logger=self.logger(),
            execution_repository=self.execution_repository,
        )

    def _build_dataset(
        self,
        status: DatasetStatus | str = DatasetStatus.PREPARED,
        prepared_object_key: str | None = "datasets/prepared.parquet",
        rows_count: int | None = 10,
        user_id: int | None = 37,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            id=self.dataset_id,
            user_id=user_id,
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

        result = await self.workflow.execute(request, user_id=37)

        self.execution_repository.record_success.assert_awaited_once_with(
            user_id=37, dataset_id=self.dataset_id,
        )
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
            await self.workflow.execute(request, user_id=37)

        assert error.value.status_code == 404
        assert error.value.message == (f"Dataset {self.dataset_id} was not found.")

        self.storage_adapter.read_file.assert_not_awaited()
        self.query_adapter.execute.assert_not_called()
        self.execution_repository.record_success.assert_not_awaited()

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
            await self.workflow.execute(request, user_id=37)

        assert error.value.status_code == 409
        assert error.value.message == (
            "Dataset must be prepared or profiled before analysis."
        )

        self.storage_adapter.read_file.assert_not_awaited()
        self.query_adapter.execute.assert_not_called()
        self.execution_repository.record_success.assert_not_awaited()

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
            await self.workflow.execute(request, user_id=37)

        assert error.value.status_code == 409
        assert error.value.message == (
            "Dataset does not have a prepared object available."
        )

        self.storage_adapter.read_file.assert_not_awaited()
        self.query_adapter.execute.assert_not_called()
        self.execution_repository.record_success.assert_not_awaited()

    @pytest.mark.anyio
    async def test_execute_should_reject_unsafe_sql(self) -> None:
        dataset = self._build_dataset()

        self.dataset_repository.get_by_id.return_value = dataset

        request = AnalysisQueryInput(
            dataset_id=self.dataset_id,
            sql="DELETE FROM dataset",
        )

        with pytest.raises(AppException) as error:
            await self.workflow.execute(request, user_id=37)

        assert error.value.status_code == 422
        assert error.value.message == ("Only SELECT statements are allowed.")

        self.query_adapter.execute.assert_not_called()
        self.execution_repository.record_success.assert_not_awaited()

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
            await self.workflow.execute(request, user_id=37)

        assert error.value.status_code == 422
        assert error.value.message == (
            "Natural-language query generation is not available yet. "
            "Provide a direct SQL query for analysis."
        )

        self.query_adapter.execute.assert_not_called()
        self.execution_repository.record_success.assert_not_awaited()

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

        result = await self.workflow.execute(request, user_id=37)

        self.execution_repository.record_success.assert_awaited_once_with(
            user_id=37, dataset_id=self.dataset_id,
        )
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

        result = await self.workflow.execute(request, user_id=37)

        self.execution_repository.record_success.assert_awaited_once_with(
            user_id=37, dataset_id=self.dataset_id,
        )
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

        result = await self.workflow.execute(request, user_id=37)

        self.execution_repository.record_success.assert_awaited_once_with(
            user_id=37, dataset_id=self.dataset_id,
        )
        assert result.limit == 20

        self.query_adapter.execute.assert_called_once_with(
            parquet_content=b"parquet-content",
            sql="SELECT id FROM dataset",
            limit=20,
        )

    @pytest.mark.parametrize("owner_id", [23, None])
    @pytest.mark.parametrize("status", [DatasetStatus.PREPARED, DatasetStatus.COMPLETED])
    async def test_rejects_unowned_dataset_before_storage_and_sql(self, owner_id, status):
        self.dataset_repository.get_by_id.return_value = self._build_dataset(
            user_id=owner_id, status=status,
        )
        self.workflow.sql_validator = Mock()
        request = AnalysisQueryInput(dataset_id=self.dataset_id, sql="DELETE FROM dataset")

        with pytest.raises(AppException) as error:
            await self.workflow.execute(request, user_id=37)

        assert error.value.status_code == 403
        assert error.value.message == "You do not have access to this dataset."
        self.dataset_repository.get_by_id.assert_awaited_once_with(self.dataset_id)
        self.storage_adapter.read_file.assert_not_awaited()
        self.workflow.sql_validator.validate.assert_not_called()
        self.query_adapter.execute.assert_not_called()
        self.execution_repository.record_success.assert_not_awaited()

    @pytest.mark.parametrize("limit, expected", [(None, 20), (101, 100)])
    async def test_normalizes_workflow_limit(self, limit, expected):
        self.dataset_repository.get_by_id.return_value = self._build_dataset()
        self.query_adapter.execute.return_value = DuckDBQueryResult(
            columns=[], rows=[], rows_count=0, returned_rows_count=0,
        )
        result = await self.workflow.execute(
            AnalysisQueryInput(dataset_id=self.dataset_id, sql="SELECT * FROM dataset", limit=limit),
            user_id=37,
        )
        self.execution_repository.record_success.assert_awaited_once_with(
            user_id=37, dataset_id=self.dataset_id,
        )
        assert result.limit == expected
        assert self.query_adapter.execute.call_args.kwargs["limit"] == expected

    @pytest.mark.parametrize("limit", [0, -1])
    async def test_rejects_nonpositive_workflow_limit(self, limit):
        with pytest.raises(AppException) as error:
            await self.workflow.execute(
                AnalysisQueryInput(dataset_id=self.dataset_id, sql="SELECT * FROM dataset", limit=limit),
                user_id=37,
            )
        assert error.value.status_code == 422
        self.dataset_repository.get_by_id.assert_not_awaited()
        self.storage_adapter.read_file.assert_not_awaited()
        self.query_adapter.execute.assert_not_called()
        self.execution_repository.record_success.assert_not_awaited()

    @pytest.mark.parametrize("stage", ["storage", "sql", "persistence"])
    async def test_failures_do_not_return_success(self, stage):
        self.dataset_repository.get_by_id.return_value = self._build_dataset()
        self.query_adapter.execute.return_value = DuckDBQueryResult(
            columns=[], rows=[], rows_count=0, returned_rows_count=0,
        )
        operation = {"storage": self.storage_adapter.read_file,
                     "sql": self.query_adapter.execute,
                     "persistence": self.execution_repository.record_success}[stage]
        error = RuntimeError("operation failed")
        operation.side_effect = error
        with pytest.raises(RuntimeError) as caught:
            await self.workflow.execute(
                AnalysisQueryInput(dataset_id=self.dataset_id, sql="SELECT * FROM dataset"),
                user_id=37,
            )
        assert caught.value is error
        if stage == "persistence":
            self.query_adapter.execute.assert_called_once()
            self.execution_repository.record_success.assert_awaited_once_with(
                user_id=37, dataset_id=self.dataset_id,
            )
        else:
            self.execution_repository.record_success.assert_not_awaited()

    async def test_repeated_sql_records_each_success(self):
        self.dataset_repository.get_by_id.return_value = self._build_dataset()
        self.query_adapter.execute.return_value = DuckDBQueryResult(
            columns=[], rows=[], rows_count=0, returned_rows_count=0,
        )
        request = AnalysisQueryInput(dataset_id=self.dataset_id, sql="SELECT * FROM dataset")
        for _ in range(2):
            result = await self.workflow.execute(request, user_id=37)
            assert result.returned_rows_count == 0
        assert self.query_adapter.execute.call_count == 2
        assert self.execution_repository.record_success.await_args_list == [
            call(user_id=37, dataset_id=self.dataset_id),
            call(user_id=37, dataset_id=self.dataset_id),
        ]
