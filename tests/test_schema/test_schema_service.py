import unittest

from app.routes.schema.services.service import DatasetSchemaService
from tests.helpers import DATASET_ID


class FakeSchemaWorkflow:
    def __init__(self, response):
        self.response = response
        self.received_dataset_id = None

    async def execute(self, dataset_id):
        self.received_dataset_id = dataset_id
        return self.response


class DatasetSchemaServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_dataset_schema_delegates_to_workflow(self):
        expected_response = object()
        workflow = FakeSchemaWorkflow(expected_response)
        service = DatasetSchemaService(workflow)

        response = await service.get_dataset_schema(DATASET_ID)

        self.assertIs(response, expected_response)
        self.assertEqual(workflow.received_dataset_id, DATASET_ID)


if __name__ == "__main__":
    unittest.main()
