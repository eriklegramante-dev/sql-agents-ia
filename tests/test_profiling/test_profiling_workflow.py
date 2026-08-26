from io import BytesIO
import unittest
from unittest.mock import patch

import pandas as pd

from app.core.profiling.workflow import DatasetProfileWorkflow
from app.enums.dataset_status import DatasetStatus
from app.prepare.exceptions import (
    ConflictException,
    NotFoundException,
    ProcessingException,
)
from tests.helpers import DATASET_ID, FakeStorage, FixedDatetime, make_dataset


class FakeProfileRepository:
    def __init__(self, dataset=None):
        self.dataset = dataset
        self.status_updates = []
        self.saved_profile = None

    async def get_by_id(self, dataset_id):
        return self.dataset

    async def update_status(self, dataset_id, status, error_message=None):
        self.status_updates.append((dataset_id, status, error_message))
        return True

    async def save_profile(self, dataset_id, profile):
        self.saved_profile = (dataset_id, profile)
        return True


class FakeProfileCalculator:
    def __init__(self, profile=None, exception=None):
        self.profile = profile or make_profile()
        self.exception = exception
        self.received_dataframe = None

    def calculate(self, dataframe):
        self.received_dataframe = dataframe

        if self.exception is not None:
            raise self.exception

        return self.profile


def make_profile():
    return {
        "rows_count": 2,
        "columns_count": 2,
        "columns": [
            {
                "name": "amount",
                "type": "numeric",
                "nullable": False,
                "null_count": 0,
                "null_percentage": 0.0,
                "cardinality": 2,
                "statistics": {"mean": 15.25},
            }
        ],
        "nulls_summary": {
            "total_nulls": 0,
            "columns_with_nulls": 0,
        },
        "cardinality_summary": {
            "high_cardinality_columns": ["amount"],
            "low_cardinality_columns": [],
        },
        "basic_statistics": {"rows": 2},
        "quality_warnings": [],
    }


def make_parquet_bytes():
    dataframe = pd.DataFrame(
        {
            "amount": [10.5, 20.0],
            "paid": [True, False],
        }
    )
    buffer = BytesIO()
    dataframe.to_parquet(buffer, index=False)
    return buffer.getvalue()


class DatasetProfileWorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_profiles_prepared_dataset_and_persists_profile(self):
        repository = FakeProfileRepository(
            make_dataset(
                status=DatasetStatus.PREPARED,
                prepared_object_key=f"{DATASET_ID}/prepared.parquet",
            )
        )
        storage = FakeStorage(
            {("prepared", f"{DATASET_ID}/prepared.parquet"): make_parquet_bytes()}
        )
        calculator = FakeProfileCalculator()
        workflow = DatasetProfileWorkflow(repository, storage, calculator)

        with patch("app.core.profiling.workflow.datetime", FixedDatetime):
            response = await workflow.execute(DATASET_ID)

        self.assertEqual(response.success, True)
        self.assertEqual(response.message, "Dataset profiled successfully.")
        self.assertEqual(response.data.dataset_id, DATASET_ID)
        self.assertEqual(response.data.status, DatasetStatus.PROFILED.value)
        self.assertEqual(response.data.rows_count, 2)
        self.assertEqual(response.data.columns_count, 2)
        self.assertEqual(response.data.updated_at, "2026-06-23T15:30:45")
        self.assertEqual(
            repository.status_updates,
            [
                (DATASET_ID, DatasetStatus.PROFILING, None),
                (DATASET_ID, DatasetStatus.PROFILED, None),
            ],
        )
        self.assertEqual(repository.saved_profile, (DATASET_ID, calculator.profile))
        self.assertEqual(
            calculator.received_dataframe.columns.tolist(), ["amount", "paid"]
        )

    async def test_execute_fails_when_dataset_does_not_exist(self):
        workflow = DatasetProfileWorkflow(
            FakeProfileRepository(None),
            FakeStorage(),
            FakeProfileCalculator(),
        )

        with self.assertRaises(NotFoundException):
            await workflow.execute(DATASET_ID)

    async def test_execute_rejects_dataset_that_is_not_prepared(self):
        repository = FakeProfileRepository(make_dataset(status=DatasetStatus.COMPLETED))
        workflow = DatasetProfileWorkflow(
            repository, FakeStorage(), FakeProfileCalculator()
        )

        with self.assertRaises(ConflictException):
            await workflow.execute(DATASET_ID)

        self.assertEqual(repository.status_updates, [])

    async def test_execute_rejects_prepared_dataset_without_object_key(self):
        repository = FakeProfileRepository(
            make_dataset(status=DatasetStatus.PREPARED, prepared_object_key=None)
        )
        workflow = DatasetProfileWorkflow(
            repository, FakeStorage(), FakeProfileCalculator()
        )

        with self.assertRaises(ConflictException):
            await workflow.execute(DATASET_ID)

        self.assertEqual(repository.status_updates, [])

    async def test_execute_marks_failed_when_storage_read_fails(self):
        repository = FakeProfileRepository(
            make_dataset(
                status=DatasetStatus.PREPARED,
                prepared_object_key=f"{DATASET_ID}/missing.parquet",
            )
        )
        workflow = DatasetProfileWorkflow(
            repository, FakeStorage(), FakeProfileCalculator()
        )

        with self.assertRaises(ProcessingException):
            await workflow.execute(DATASET_ID)

        self.assertEqual(
            repository.status_updates[0],
            (DATASET_ID, DatasetStatus.PROFILING, None),
        )
        self.assertEqual(repository.status_updates[1][0], DATASET_ID)
        self.assertEqual(repository.status_updates[1][1], DatasetStatus.FAILED)
        self.assertIn("missing.parquet", repository.status_updates[1][2])

    async def test_execute_marks_failed_when_calculation_fails(self):
        repository = FakeProfileRepository(
            make_dataset(
                status=DatasetStatus.PREPARED,
                prepared_object_key=f"{DATASET_ID}/prepared.parquet",
            )
        )
        storage = FakeStorage(
            {("prepared", f"{DATASET_ID}/prepared.parquet"): make_parquet_bytes()}
        )
        workflow = DatasetProfileWorkflow(
            repository,
            storage,
            FakeProfileCalculator(exception=RuntimeError("profile failed")),
        )

        with self.assertRaisesRegex(ProcessingException, "profile failed"):
            await workflow.execute(DATASET_ID)

        self.assertEqual(
            repository.status_updates,
            [
                (DATASET_ID, DatasetStatus.PROFILING, None),
                (DATASET_ID, DatasetStatus.FAILED, "profile failed"),
            ],
        )
        self.assertIsNone(repository.saved_profile)


if __name__ == "__main__":
    unittest.main()
