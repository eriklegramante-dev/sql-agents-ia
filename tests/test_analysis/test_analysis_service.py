import unittest

from app.routes.analysis.dtos.dto import AnalysisQueryRequestDTO
from app.routes.analysis.services.service import AnalysisQueryService
from tests.helpers import DATASET_ID


class FakeAnalysisWorkflow:
    def __init__(self, response):
        self.response = response
        self.received_request = None

    async def execute(self, request):
        self.received_request = request
        return self.response


class FakeLogger:
    def log_info(self, message):
        pass


class AnalysisQueryServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_delegates_to_workflow(self):
        expected_response = object()
        workflow = FakeAnalysisWorkflow(expected_response)
        service = AnalysisQueryService(workflow, logger=FakeLogger())
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            sql="select * from dataset",
            limit=5,
        )

        response = await service.execute(request)

        self.assertIs(response, expected_response)
        self.assertIs(workflow.received_request, request)


if __name__ == "__main__":
    unittest.main()
