import unittest

from app.core.profiling.workflow import DatasetProfileWorkflow
from app.routes.profiling.services.service import DatasetProfileService
from tests.helpers import DATASET_ID


class FakeProfileWorkflow:
    def __init__(self, response):
        self.response = response
        self.received_dataset_id = None

    async def execute(self, dataset_id):
        self.received_dataset_id = dataset_id
        return self.response


class DatasetProfileServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_profile_dataset_delegates_to_workflow(self):
        expected_response = object()
        workflow = FakeProfileWorkflow(expected_response)
        service = DatasetProfileService(workflow)

        response = await service.profile_dataset(DATASET_ID)

        self.assertIs(response, expected_response)
        self.assertEqual(workflow.received_dataset_id, DATASET_ID)

    async def test_profile_service_default_workflow_does_not_use_missing_factory(self):
        service = DatasetProfileService()

        self.assertIsInstance(service.workflow, DatasetProfileWorkflow)


if __name__ == "__main__":
    unittest.main()
