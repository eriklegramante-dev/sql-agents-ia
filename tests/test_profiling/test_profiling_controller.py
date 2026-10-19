import unittest

from app.routes.profiling.controllers.controller import DatasetProfileController
from app.routes.profiling.dtos.dto import (
    DatasetProfileResponseDTO,
    DatasetProfileResponseDataDTO,
)
from tests.helpers import DATASET_ID


class FakeProfileService:
    def __init__(self, response):
        self.response = response
        self.received_dataset_id = None

    async def profile_dataset(self, dataset_id, *, user_id: int):
        self.received_dataset_id = dataset_id
        self.received_user_id = user_id
        return self.response


class DatasetProfileControllerTest(unittest.IsolatedAsyncioTestCase):
    async def test_profile_dataset_delegates_to_service(self):
        expected_response = DatasetProfileResponseDTO(
            success=True,
            message="Dataset profiled successfully.",
            data=DatasetProfileResponseDataDTO(
                dataset_id=DATASET_ID,
                status="PROFILED",
                rows_count=2,
                columns_count=1,
                columns=[
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
                nulls_summary={
                    "total_nulls": 0,
                    "columns_with_nulls": 0,
                },
                cardinality_summary={
                    "high_cardinality_columns": ["amount"],
                    "low_cardinality_columns": [],
                },
                basic_statistics={"rows": 2},
                quality_warnings=[],
                updated_at="2026-06-23T15:30:45",
            ),
        )
        service = FakeProfileService(expected_response)
        controller = DatasetProfileController(service)

        response = await controller.profile_dataset(DATASET_ID, user_id=17)

        self.assertIs(response, expected_response)
        self.assertEqual(service.received_dataset_id, DATASET_ID)
        self.assertEqual(service.received_user_id, 17)


if __name__ == "__main__":
    unittest.main()
