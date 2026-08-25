import unittest

from app.core.analysis.models import AnalysisQueryInput, AnalysisQueryOutput
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
    async def test_execute_maps_request_to_workflow_and_returns_response_dto(self):
        workflow_response = AnalysisQueryOutput(
            dataset_id=DATASET_ID,
            executed_sql="select * from dataset",
            columns=["id", "name"],
            rows=[{"id": 1, "name": "Ana"}],
            rows_count=1,
            returned_rows_count=1,
            limit=5,
        )
        workflow = FakeAnalysisWorkflow(workflow_response)
        service = AnalysisQueryService(workflow, logger=FakeLogger())
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            sql="select * from dataset",
            limit=5,
        )

        response = await service.execute(request)

        self.assertIsInstance(workflow.received_request, AnalysisQueryInput)
        self.assertEqual(workflow.received_request.dataset_id, DATASET_ID)
        self.assertIsNone(workflow.received_request.question)
        self.assertEqual(workflow.received_request.sql, "select * from dataset")
        self.assertEqual(workflow.received_request.limit, 5)

        self.assertEqual(response.dataset_id, DATASET_ID)
        self.assertEqual(response.executed_sql, "select * from dataset")
        self.assertEqual(response.columns, ["id", "name"])
        self.assertEqual(response.rows, [{"id": 1, "name": "Ana"}])
        self.assertEqual(response.rows_count, 1)
        self.assertEqual(response.returned_rows_count, 1)
        self.assertEqual(response.limit, 5)


if __name__ == "__main__":
    unittest.main()
