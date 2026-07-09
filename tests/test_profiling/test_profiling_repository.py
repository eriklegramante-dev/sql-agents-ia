import json
import unittest

from app.database.dataset_repository import DatasetRepository
from tests.helpers import DATASET_ID


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
    def __init__(self, execute_result="INSERT 0 1"):
        self.execute_result = execute_result
        self.execute_calls = []

    async def execute(self, query, *args):
        self.execute_calls.append((query, args))
        return self.execute_result


class DatasetProfileRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_save_profile_serializes_profile_as_json(self):
        connection = FakeConnection()
        repository = DatasetRepository(FakePool(connection))
        profile = {
            "rows_count": 2,
            "columns_count": 1,
            "columns": [{"name": "amount", "type": "numeric"}],
        }

        saved = await repository.save_profile(DATASET_ID, profile)

        self.assertTrue(saved)
        self.assertEqual(connection.execute_calls[0][1][0], DATASET_ID)
        self.assertEqual(json.loads(connection.execute_calls[0][1][1]), profile)
        self.assertIn("ON CONFLICT (dataset_id)", connection.execute_calls[0][0])

    async def test_save_profile_returns_true_when_existing_profile_is_updated(self):
        connection = FakeConnection(execute_result="UPDATE 1")
        repository = DatasetRepository(FakePool(connection))

        saved = await repository.save_profile(DATASET_ID, {"rows_count": 2})

        self.assertTrue(saved)

    async def test_save_profile_returns_false_when_no_row_is_written(self):
        connection = FakeConnection(execute_result="UPDATE 0")
        repository = DatasetRepository(FakePool(connection))

        saved = await repository.save_profile(DATASET_ID, {"rows_count": 2})

        self.assertFalse(saved)


if __name__ == "__main__":
    unittest.main()
