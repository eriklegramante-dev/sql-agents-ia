import unittest

from app.routes.schema.controllers.controller import DatasetSchemaController
from app.routes.schema.dtos.dto import (
    DatasetSchemaColumnDTO,
    DatasetSchemaResponseDataDTO,
)
from tests.helpers import DATASET_ID, NOW


class FakeSchemaService:
    def __init__(self, response):
        self.response = response
        self.received_dataset_id = None

    async def get_dataset_schema(self, dataset_id):
        self.received_dataset_id = dataset_id
        return self.response


class DatasetSchemaControllerTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_dataset_schema_returns_success_payload(self):
        response_data = DatasetSchemaResponseDataDTO(
            dataset_id=DATASET_ID,
            status="PREPARED",
            columns_count=1,
            schema_columns=[
                DatasetSchemaColumnDTO(
                    name="amount",
                    original_name="Amount",
                    type="numeric",
                    nullable=False,
                    sample_values=["10", "20"],
                    warnings=[],
                )
            ],
            updated_at=NOW,
        )
        service = FakeSchemaService(response_data)
        controller = DatasetSchemaController(service)

        result = await controller.get_dataset_schema(DATASET_ID)

        self.assertEqual(service.received_dataset_id, DATASET_ID)
        self.assertEqual(result["success"], True)
        self.assertEqual(result["message"], "Dataset schema retrieved successfully.")
        self.assertIsNone(result["errors"])
        self.assertEqual(result["data"]["dataset_id"], str(DATASET_ID))
        self.assertEqual(result["data"]["schema"][0]["name"], "amount")


if __name__ == "__main__":
    unittest.main()
