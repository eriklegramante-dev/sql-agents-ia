from io import BytesIO
import unittest
from unittest.mock import patch

import pandas as pd

from app.prepare.exceptions import ConflictException, NotFoundException, StorageException
from app.enums.dataset_status import DatasetStatus
from app.core.prepare.workflow import DatasetPreparationWorkflow
from tests.helpers import (
    DATASET_ID,
    FakeDatasetRepository,
    FakeStorage,
    FixedDatetime,
    make_dataset,
)


class DatasetPreparationWorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_prepares_dataset_and_persists_schema(self):
        raw_csv = b"Amount,Paid\n10.5,yes\n20,no\n"
        repository = FakeDatasetRepository(make_dataset())
        storage = FakeStorage({("raw", "uploads/input.csv"): raw_csv})
        workflow = DatasetPreparationWorkflow(repository, storage)

        with patch("app.core.prepare.workflow.datetime", FixedDatetime):
            response = await workflow.execute(DATASET_ID)

        expected_key = f"{DATASET_ID}/prepared_20260623_153045.parquet"
        self.assertEqual(response.dataset_id, DATASET_ID)
        self.assertEqual(response.status, DatasetStatus.PREPARED.value)
        self.assertEqual(response.prepared_object_key, expected_key)
        self.assertEqual(response.rows_count, 2)
        self.assertEqual(response.columns_count, 2)
        self.assertEqual(
            repository.status_updates,
            [(DATASET_ID, DatasetStatus.PREPARING, None)],
        )
        self.assertEqual(repository.saved_schema[0], DATASET_ID)
        self.assertEqual(
            [column.name for column in repository.saved_schema[1]],
            ["amount", "paid"],
        )
        self.assertEqual(
            repository.prepared_info,
            (DATASET_ID, expected_key, 2, 2),
        )

        self.assertEqual(len(storage.writes), 1)
        written_container, written_path, written_data = storage.writes[0]
        self.assertEqual(written_container, "prepared")
        self.assertEqual(written_path, expected_key)
        written_df = pd.read_parquet(BytesIO(written_data), engine="pyarrow")
        self.assertEqual(written_df.columns.tolist(), ["amount", "paid"])

    async def test_execute_fails_when_dataset_does_not_exist(self):
        workflow = DatasetPreparationWorkflow(FakeDatasetRepository(None), FakeStorage())

        with self.assertRaises(NotFoundException):
            await workflow.execute(DATASET_ID)

    async def test_execute_rejects_dataset_that_is_not_completed(self):
        repository = FakeDatasetRepository(make_dataset(status=DatasetStatus.UPLOADING))
        workflow = DatasetPreparationWorkflow(repository, FakeStorage())

        with self.assertRaises(ConflictException):
            await workflow.execute(DATASET_ID)

        self.assertEqual(repository.status_updates, [])

    async def test_execute_marks_failed_when_raw_file_is_missing(self):
        repository = FakeDatasetRepository(make_dataset())
        workflow = DatasetPreparationWorkflow(repository, FakeStorage())

        with self.assertRaises(StorageException):
            await workflow.execute(DATASET_ID)

        self.assertEqual(
            repository.status_updates[0],
            (DATASET_ID, DatasetStatus.PREPARING, None),
        )
        self.assertEqual(repository.status_updates[1][0], DATASET_ID)
        self.assertEqual(repository.status_updates[1][1], DatasetStatus.FAILED)
        self.assertIn("uploads/input.csv", repository.status_updates[1][2])

    async def test_execute_marks_failed_and_reraises_generic_exception(self):
        raw_csv = b"Amount\n10\n"
        repository = FakeDatasetRepository(make_dataset())
        storage = FakeStorage({("raw", "uploads/input.csv"): raw_csv})
        workflow = DatasetPreparationWorkflow(repository, storage)

        with patch(
            "app.core.prepare.workflow.SchemaInferer.process_dataframe",
            side_effect=RuntimeError("schema failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "schema failed"):
                await workflow.execute(DATASET_ID)

        self.assertEqual(
            repository.status_updates[0],
            (DATASET_ID, DatasetStatus.PREPARING, None),
        )
        self.assertEqual(
            repository.status_updates[1],
            (DATASET_ID, DatasetStatus.FAILED, "schema failed"),
        )
        self.assertEqual(storage.writes, [])


if __name__ == "__main__":
    unittest.main()
