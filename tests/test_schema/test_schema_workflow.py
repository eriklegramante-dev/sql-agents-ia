import unittest

from app.core.schema.workflow import DatasetSchemaWorkflow
from app.enums.dataset_status import DatasetStatus
from app.models.dataset_schema_table import ColumnSchema
from app.prepare.exceptions import ConflictException, NotFoundException
from tests.helpers import DATASET_ID, make_dataset


class FakeSchemaRepository:
    def __init__(self, dataset=None, schema=None):
        self.dataset = dataset
        self.schema = schema
        self.received_dataset_id = None
        self.received_schema_dataset_id = None

    async def get_by_id(self, dataset_id):
        self.received_dataset_id = dataset_id
        return self.dataset

    async def get_schema(self, dataset_id):
        self.received_schema_dataset_id = dataset_id
        return self.schema


class DatasetSchemaWorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_persisted_schema_for_prepared_dataset(self):
        schema = [
            ColumnSchema(
                name="amount",
                original_name="Amount",
                data_type="numeric",
                nullable=False,
                sample_values=["10", "20"],
                warnings=[],
            ),
            ColumnSchema(
                name="paid",
                original_name="Paid",
                data_type="boolean",
                nullable=True,
                sample_values=["true"],
                warnings=["empty values converted to null"],
            ),
        ]
        repository = FakeSchemaRepository(
            dataset=make_dataset(
                status=DatasetStatus.PREPARED,
                prepared_object_key=f"{DATASET_ID}/prepared.parquet",
                rows_count=2,
                columns_count=2,
            ),
            schema=schema,
        )
        workflow = DatasetSchemaWorkflow(repository)

        response = await workflow.execute(DATASET_ID)

        self.assertEqual(repository.received_dataset_id, DATASET_ID)
        self.assertEqual(repository.received_schema_dataset_id, DATASET_ID)
        self.assertEqual(response.dataset_id, DATASET_ID)
        self.assertEqual(response.status, DatasetStatus.PREPARED.value)
        self.assertEqual(response.columns_count, 2)
        self.assertEqual(response.schema_columns[0].name, "amount")
        self.assertEqual(response.schema_columns[0].type, "numeric")
        self.assertEqual(
            response.schema_columns[1].warnings,
            ["empty values converted to null"],
        )

    async def test_execute_fails_when_dataset_does_not_exist(self):
        workflow = DatasetSchemaWorkflow(FakeSchemaRepository(dataset=None))

        with self.assertRaises(NotFoundException):
            await workflow.execute(DATASET_ID)

    async def test_execute_fails_when_schema_does_not_exist(self):
        repository = FakeSchemaRepository(
            dataset=make_dataset(status=DatasetStatus.PREPARED),
            schema=None,
        )
        workflow = DatasetSchemaWorkflow(repository)

        with self.assertRaises(NotFoundException):
            await workflow.execute(DATASET_ID)

    async def test_execute_rejects_dataset_that_is_not_prepared(self):
        repository = FakeSchemaRepository(
            dataset=make_dataset(status=DatasetStatus.COMPLETED),
            schema=[
                ColumnSchema(
                    name="amount",
                    original_name="Amount",
                    data_type="numeric",
                    nullable=False,
                )
            ],
        )
        workflow = DatasetSchemaWorkflow(repository)

        with self.assertRaises(ConflictException):
            await workflow.execute(DATASET_ID)


if __name__ == "__main__":
    unittest.main()
