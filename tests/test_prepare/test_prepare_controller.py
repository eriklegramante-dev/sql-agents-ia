import unittest

from app.models.dataset_schema_table import ColumnSchema
from app.routes.prepare.controllers.controller import DatasetPreparationController
from app.routes.prepare.dtos.dto import DatasetPreparationResponseData
from tests.helpers import DATASET_ID, NOW


class FakePreparationService:
    def __init__(self, response):
        self.response = response
        self.received_dataset_id = None

    async def prepare_dataset(self, dataset_id):
        self.received_dataset_id = dataset_id
        return self.response


class DatasetPreparationControllerTest(unittest.IsolatedAsyncioTestCase):
    async def test_prepare_dataset_returns_success_payload(self):
        response_data = DatasetPreparationResponseData(
            dataset_id=DATASET_ID,
            status="PREPARED",
            raw_object_key="uploads/input.csv",
            prepared_object_key=f"{DATASET_ID}/prepared.parquet",
            rows_count=2,
            columns_count=1,
            columns_schema=[
                ColumnSchema(
                    name="amount",
                    original_name="Amount",
                    data_type="numeric",
                    nullable=False,
                    sample_values=["10", "20"],
                )
            ],
            updated_at=NOW,
        )
        service = FakePreparationService(response_data)
        controller = DatasetPreparationController(service)

        result = await controller.prepare_dataset(DATASET_ID)

        self.assertEqual(service.received_dataset_id, DATASET_ID)
        self.assertEqual(result["success"], True)
        self.assertEqual(result["message"], "Dataset prepared successfully")
        self.assertEqual(result["errors"], None)
        self.assertEqual(result["data"]["dataset_id"], str(DATASET_ID))
        self.assertEqual(result["data"]["schema"][0]["name"], "amount")


if __name__ == "__main__":
    unittest.main()
