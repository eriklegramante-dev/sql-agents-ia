import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.adapters.storage.local_storage_adapter import LocalStorageAdapter
from app.database.dataset_repository import DatasetRepository
from app.enums.dataset_status import DatasetStatus
from app.models.dataset_schema_table import ColumnSchema
from app.prepare import dependencies
from app.routes.prepare.controllers.controller import DatasetPreparationController
from app.routes.prepare.services.service import DatasetPreparationService
from app.core.prepare.workflow import DatasetPreparationWorkflow
from tests.helpers import DATASET_ID, NOW


class FakeAcquireContext:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakePool:
    def __init__(self, connection):
        self.connection = connection
        self.acquire_calls = 0

    def acquire(self):
        self.acquire_calls += 1
        return FakeAcquireContext(self.connection)


class FakeConnection:
    def __init__(self, fetchrow_result=None, execute_result="UPDATE 1"):
        self.fetchrow_result = fetchrow_result
        self.execute_result = execute_result
        self.fetchrow_calls = []
        self.execute_calls = []

    async def fetchrow(self, query, *args):
        self.fetchrow_calls.append((query, args))
        return self.fetchrow_result

    async def execute(self, query, *args):
        self.execute_calls.append((query, args))
        return self.execute_result


def make_dataset_row(**overrides):
    row = {
        "id": DATASET_ID,
        "name": "dataset.csv",
        "status": DatasetStatus.COMPLETED.value,
        "raw_object_key": "uploads/input.csv",
        "prepared_object_key": None,
        "rows_count": None,
        "columns_count": None,
        "error_message": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    row.update(overrides)
    return row


def make_settings(storage_type="local", local_storage_path="./storage"):
    return SimpleNamespace(
        database=SimpleNamespace(
            host="localhost",
            port=5432,
            name="sql_agents",
            user="postgres",
            password="password",
            min_pool_size=1,
            max_pool_size=5,
        ),
        storage=SimpleNamespace(
            storage_type=storage_type,
            azure_storage_connection_string="UseDevelopmentStorage=true",
            local_storage_path=local_storage_path,
        ),
    )


class LocalStorageAdapterTest(unittest.IsolatedAsyncioTestCase):
    async def test_write_read_exists_and_delete_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            storage = LocalStorageAdapter(temporary_directory)

            object_key = await storage.write_file(
                "raw",
                "uploads/input.csv",
                b"col\nvalue\n",
            )

            self.assertEqual(object_key, "uploads/input.csv")
            self.assertTrue(await storage.file_exists("raw", "uploads/input.csv"))
            self.assertEqual(
                await storage.read_file("raw", "uploads/input.csv"),
                b"col\nvalue\n",
            )
            self.assertTrue(await storage.delete_file("raw", "uploads/input.csv"))
            self.assertFalse(await storage.file_exists("raw", "uploads/input.csv"))

    async def test_read_file_raises_when_file_does_not_exist(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            storage = LocalStorageAdapter(temporary_directory)

            with self.assertRaisesRegex(
                FileNotFoundError,
                "File missing.csv not found in container raw",
            ):
                await storage.read_file("raw", "missing.csv")

    async def test_delete_file_returns_false_when_file_does_not_exist(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            storage = LocalStorageAdapter(temporary_directory)

            deleted = await storage.delete_file("raw", "missing.csv")

            self.assertFalse(deleted)


class PrepareDependenciesTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        dependencies._db_pool = None

    def tearDown(self):
        dependencies._db_pool = None

    async def test_get_db_pool_creates_and_reuses_pool(self):
        expected_pool = object()

        with (
            patch(
                "app.prepare.dependencies.get_settings",
                return_value=make_settings(),
            ),
            patch(
                "app.prepare.dependencies.asyncpg.create_pool",
                new=AsyncMock(return_value=expected_pool),
            ) as create_pool,
        ):
            first_pool = await dependencies.get_db_pool()
            second_pool = await dependencies.get_db_pool()

        self.assertIs(first_pool, expected_pool)
        self.assertIs(second_pool, expected_pool)
        create_pool.assert_awaited_once_with(
            host="localhost",
            port=5432,
            database="sql_agents",
            user="postgres",
            password="password",
            min_size=1,
            max_size=5,
        )

    async def test_get_dataset_repository_uses_shared_pool(self):
        expected_pool = object()

        with patch(
            "app.prepare.dependencies.get_db_pool",
            new=AsyncMock(return_value=expected_pool),
        ):
            repository = await dependencies.get_dataset_repository()

        self.assertIsInstance(repository, DatasetRepository)
        self.assertIs(repository.pool, expected_pool)

    async def test_get_storage_adapter_returns_local_adapter(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch(
                "app.prepare.dependencies.get_settings",
                return_value=make_settings(local_storage_path=temporary_directory),
            ):
                storage = await dependencies.get_storage_adapter()

            self.assertIsInstance(storage, LocalStorageAdapter)
            self.assertEqual(str(storage.base_path), temporary_directory)

    async def test_get_storage_adapter_returns_blob_adapter_for_azure(self):
        fake_blob_adapter = object()

        with (
            patch(
                "app.prepare.dependencies.get_settings",
                return_value=make_settings(storage_type="azure"),
            ),
            patch(
                "app.prepare.dependencies.BlobStorageAdapter",
                Mock(return_value=fake_blob_adapter),
            ) as blob_adapter,
        ):
            storage = await dependencies.get_storage_adapter()

        self.assertIs(storage, fake_blob_adapter)
        blob_adapter.assert_called_once_with("UseDevelopmentStorage=true")

    async def test_get_dataset_preparation_controller_wires_dependencies(self):
        repository = object()
        storage = object()

        with (
            patch(
                "app.prepare.dependencies.get_dataset_repository",
                new=AsyncMock(return_value=repository),
            ),
            patch(
                "app.prepare.dependencies.get_storage_adapter",
                new=AsyncMock(return_value=storage),
            ),
        ):
            controller = await dependencies.get_dataset_preparation_controller()

        self.assertIsInstance(controller, DatasetPreparationController)
        self.assertIsInstance(controller.service, DatasetPreparationService)
        self.assertIsInstance(controller.service.workflow, DatasetPreparationWorkflow)
        self.assertIs(controller.service.workflow.repository, repository)
        self.assertIs(controller.service.workflow.storage, storage)


class DatasetRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_by_id_returns_dataset_table_when_row_exists(self):
        connection = FakeConnection(fetchrow_result=make_dataset_row())
        repository = DatasetRepository(FakePool(connection))

        dataset = await repository.get_by_id(DATASET_ID)

        self.assertEqual(dataset.id, DATASET_ID)
        self.assertEqual(dataset.name, "dataset.csv")
        self.assertEqual(dataset.status, DatasetStatus.COMPLETED)
        self.assertEqual(dataset.raw_object_key, "uploads/input.csv")
        self.assertEqual(connection.fetchrow_calls[0][1], (DATASET_ID,))

    async def test_get_by_id_returns_none_when_row_does_not_exist(self):
        connection = FakeConnection(fetchrow_result=None)
        repository = DatasetRepository(FakePool(connection))

        dataset = await repository.get_by_id(DATASET_ID)

        self.assertIsNone(dataset)

    async def test_update_status_returns_true_when_one_row_is_updated(self):
        connection = FakeConnection(execute_result="UPDATE 1")
        repository = DatasetRepository(FakePool(connection))

        updated = await repository.update_status(
            DATASET_ID,
            DatasetStatus.FAILED,
            "invalid file",
        )

        self.assertTrue(updated)
        self.assertEqual(
            connection.execute_calls[0][1],
            (DATASET_ID, DatasetStatus.FAILED.value, "invalid file"),
        )

    async def test_update_status_returns_false_when_no_row_is_updated(self):
        connection = FakeConnection(execute_result="UPDATE 0")
        repository = DatasetRepository(FakePool(connection))

        updated = await repository.update_status(DATASET_ID, DatasetStatus.PREPARING)

        self.assertFalse(updated)

    async def test_update_prepared_info_returns_updated_dataset(self):
        connection = FakeConnection(
            fetchrow_result=make_dataset_row(
                status=DatasetStatus.PREPARED.value,
                prepared_object_key="prepared/output.parquet",
                rows_count=10,
                columns_count=3,
            )
        )
        repository = DatasetRepository(FakePool(connection))

        dataset = await repository.update_prepared_info(
            DATASET_ID,
            "prepared/output.parquet",
            10,
            3,
        )

        self.assertEqual(dataset.status, DatasetStatus.PREPARED)
        self.assertEqual(dataset.prepared_object_key, "prepared/output.parquet")
        self.assertEqual(dataset.rows_count, 10)
        self.assertEqual(dataset.columns_count, 3)
        self.assertEqual(
            connection.fetchrow_calls[0][1],
            (
                DATASET_ID,
                DatasetStatus.PREPARED.value,
                "prepared/output.parquet",
                10,
                3,
            ),
        )

    async def test_update_prepared_info_returns_none_when_row_does_not_exist(self):
        connection = FakeConnection(fetchrow_result=None)
        repository = DatasetRepository(FakePool(connection))

        dataset = await repository.update_prepared_info(
            DATASET_ID,
            "prepared/output.parquet",
            10,
            3,
        )

        self.assertIsNone(dataset)

    async def test_save_schema_serializes_columns_as_json(self):
        connection = FakeConnection()
        repository = DatasetRepository(FakePool(connection))
        schema = [
            ColumnSchema(
                name="amount",
                original_name="Amount",
                data_type="float",
                nullable=False,
                sample_values=["10.5"],
                warnings=["coerced"],
            )
        ]

        saved = await repository.save_schema(DATASET_ID, schema)

        self.assertTrue(saved)
        self.assertEqual(connection.execute_calls[0][1][0], DATASET_ID)
        serialized_columns = json.loads(connection.execute_calls[0][1][1])
        self.assertEqual(
            serialized_columns,
            [
                {
                    "name": "amount",
                    "original_name": "Amount",
                    "data_type": "float",
                    "nullable": False,
                }
            ],
        )

    async def test_get_schema_returns_column_schema_from_json_string(self):
        connection = FakeConnection(
            fetchrow_result={
                "columns": json.dumps(
                    [
                        {
                            "name": "amount",
                            "original_name": "Amount",
                            "type": "float",
                            "nullable": False,
                        }
                    ]
                )
            }
        )
        repository = DatasetRepository(FakePool(connection))

        schema = await repository.get_schema(DATASET_ID)

        self.assertEqual(len(schema), 1)
        self.assertEqual(schema[0].name, "amount")
        self.assertEqual(schema[0].data_type, "float")
        self.assertFalse(schema[0].nullable)

    async def test_get_schema_returns_column_schema_from_json_value(self):
        connection = FakeConnection(
            fetchrow_result={
                "columns": [
                    {
                        "name": "paid",
                        "original_name": "Paid",
                        "type": "boolean",
                        "nullable": True,
                    }
                ]
            }
        )
        repository = DatasetRepository(FakePool(connection))

        schema = await repository.get_schema(DATASET_ID)

        self.assertEqual(schema[0].name, "paid")
        self.assertEqual(schema[0].data_type, "boolean")
        self.assertTrue(schema[0].nullable)

    async def test_get_schema_returns_none_when_row_does_not_exist(self):
        connection = FakeConnection(fetchrow_result=None)
        repository = DatasetRepository(FakePool(connection))

        schema = await repository.get_schema(DATASET_ID)

        self.assertIsNone(schema)


if __name__ == "__main__":
    unittest.main()
