import unittest

from app.routes.preview.dtos.dto import DatasetPreviewRequestDTO
from app.routes.preview.services.service import DatasetPreviewService
from tests.helpers import DATASET_ID


class FakePreviewWorkflow:
    def __init__(self, response):
        self.response = response
        self.received_request = None

    async def execute(self, request):
        self.received_request = request
        return self.response


class DatasetPreviewServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_delegates_to_workflow(self):
        expected_response = object()
        workflow = FakePreviewWorkflow(expected_response)
        service = DatasetPreviewService(workflow)
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=5,
        )

        response = await service.execute(request)

        self.assertIs(response, expected_response)
        self.assertIs(workflow.received_request, request)


if __name__ == "__main__":
    unittest.main()
