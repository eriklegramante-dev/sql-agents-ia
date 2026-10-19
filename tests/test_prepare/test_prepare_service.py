import unittest

from app.routes.prepare.services.service import DatasetPreparationService
from tests.helpers import DATASET_ID


class FakePreparationWorkflow:
    def __init__(self, response):
        self.response = response
        self.received_dataset_id = None

    async def execute(self, dataset_id, *, user_id: int):
        self.received_dataset_id = dataset_id
        self.received_user_id = user_id
        return self.response


class DatasetPreparationServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_prepare_dataset_returns_workflow_response(self):
        expected_response = object()
        workflow = FakePreparationWorkflow(expected_response)
        service = DatasetPreparationService(workflow)

        response = await service.prepare_dataset(DATASET_ID, user_id=17)

        self.assertIs(response, expected_response)
        self.assertEqual(workflow.received_dataset_id, DATASET_ID)
        self.assertEqual(workflow.received_user_id, 17)


if __name__ == "__main__":
    unittest.main()
