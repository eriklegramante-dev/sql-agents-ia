import unittest

from app.core.preview.workflow import DatasetPreviewWorkflow
from app.enums.dataset_status import DatasetStatus
from app.prepare.exceptions import AppException
from app.routes.preview.dtos.dto import DatasetPreviewRequestDTO
from app.routes.preview.helpers.preview_result import PreviewResult
from tests.helpers import DATASET_ID, FakeDatasetRepository, FakeStorage, make_dataset


class FakePreviewReader:
    def __init__(self, result):
        self.result = result
        self.received_content = None
        self.received_limit = None

    def read(self, parquet_content, limit):
        self.received_content = parquet_content
        self.received_limit = limit
        return self.result


class DatasetPreviewWorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_preview_for_prepared_dataset(self):
        prepared_object_key = f"{DATASET_ID}/prepared.parquet"
        parquet_content = b"parquet-bytes"
        preview_result = PreviewResult(
            columns=["name", "age"],
            rows=[{"name": "Ana", "age": 30}],
            rows_count=3,
        )
        repository = FakeDatasetRepository(
            make_dataset(
                status=DatasetStatus.PREPARED,
                prepared_object_key=prepared_object_key,
                rows_count=10,
            )
        )
        storage = FakeStorage(
            files={("prepared", prepared_object_key): parquet_content}
        )
        reader = FakePreviewReader(preview_result)
        workflow = DatasetPreviewWorkflow(
            dataset_repository=repository,
            storage_adapter=storage,
            preview_reader=reader,
        )
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=2,
        )

        response = await workflow.execute(request)

        self.assertEqual(reader.received_content, parquet_content)
        self.assertEqual(reader.received_limit, 2)
        self.assertEqual(response.dataset_id, DATASET_ID)
        self.assertEqual(response.status, DatasetStatus.PREPARED.value)
        self.assertEqual(response.limit, 2)
        self.assertEqual(response.columns, ["name", "age"])
        self.assertEqual(response.rows, [{"name": "Ana", "age": 30}])
        self.assertEqual(response.rows_count, 10)
        self.assertEqual(response.returned_rows_count, 1)

    async def test_execute_accepts_profiled_dataset(self):
        prepared_object_key = f"{DATASET_ID}/prepared.parquet"
        workflow = DatasetPreviewWorkflow(
            dataset_repository=FakeDatasetRepository(
                make_dataset(
                    status=DatasetStatus.PROFILED,
                    prepared_object_key=prepared_object_key,
                    rows_count=None,
                )
            ),
            storage_adapter=FakeStorage(
                files={("prepared", prepared_object_key): b"parquet-bytes"}
            ),
            preview_reader=FakePreviewReader(
                PreviewResult(
                    columns=["name"],
                    rows=[{"name": "Ana"}],
                    rows_count=1,
                )
            ),
        )
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=1,
        )

        response = await workflow.execute(request)

        self.assertEqual(response.status, DatasetStatus.PROFILED.value)
        self.assertEqual(response.rows_count, 1)

    async def test_execute_caps_limit_to_maximum(self):
        prepared_object_key = f"{DATASET_ID}/prepared.parquet"
        workflow = DatasetPreviewWorkflow(
            dataset_repository=FakeDatasetRepository(
                make_dataset(
                    status=DatasetStatus.PREPARED,
                    prepared_object_key=prepared_object_key,
                )
            ),
            storage_adapter=FakeStorage(
                files={("prepared", prepared_object_key): b"parquet-bytes"}
            ),
            preview_reader=FakePreviewReader(
                PreviewResult(columns=[], rows=[], rows_count=0)
            ),
        )
        request = DatasetPreviewRequestDTO.model_construct(
            dataset_id=DATASET_ID,
            limit=150,
        )

        response = await workflow.execute(request)

        self.assertEqual(response.limit, 100)

    async def test_execute_fails_when_dataset_does_not_exist(self):
        workflow = DatasetPreviewWorkflow(
            dataset_repository=FakeDatasetRepository(dataset=None),
            storage_adapter=FakeStorage(),
        )
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=1,
        )

        with self.assertRaises(AppException) as context:
            await workflow.execute(request)

        self.assertEqual(context.exception.status_code, 404)

    async def test_execute_rejects_dataset_that_is_not_prepared(self):
        workflow = DatasetPreviewWorkflow(
            dataset_repository=FakeDatasetRepository(
                make_dataset(status=DatasetStatus.COMPLETED)
            ),
            storage_adapter=FakeStorage(),
        )
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=1,
        )

        with self.assertRaises(AppException) as context:
            await workflow.execute(request)

        self.assertEqual(context.exception.status_code, 409)

    async def test_execute_rejects_dataset_without_prepared_object(self):
        workflow = DatasetPreviewWorkflow(
            dataset_repository=FakeDatasetRepository(
                make_dataset(status=DatasetStatus.PREPARED)
            ),
            storage_adapter=FakeStorage(),
        )
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=1,
        )

        with self.assertRaises(AppException) as context:
            await workflow.execute(request)

        self.assertEqual(context.exception.status_code, 409)

    async def test_execute_requires_repository_dependency(self):
        workflow = DatasetPreviewWorkflow(
            dataset_repository=None,
            storage_adapter=FakeStorage(),
        )
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=1,
        )

        with self.assertRaisesRegex(RuntimeError, "Dataset repository"):
            await workflow.execute(request)

    async def test_execute_requires_storage_dependency(self):
        workflow = DatasetPreviewWorkflow(
            dataset_repository=FakeDatasetRepository(
                make_dataset(status=DatasetStatus.PREPARED)
            ),
            storage_adapter=None,
        )
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=1,
        )

        with self.assertRaisesRegex(RuntimeError, "Storage adapter"):
            await workflow.execute(request)


if __name__ == "__main__":
    unittest.main()
