import unittest

from fastapi import HTTPException

from app.prepare.exceptions import AppException
from app.routes.analysis.controllers.controller import AnalysisQueryController
from app.routes.analysis.dtos.dto import (
    AnalysisQueryRequestDTO,
    AnalysisQueryResponseDataDTO,
)
from tests.helpers import DATASET_ID


class FakeAnalysisService:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_request = None

    async def execute(self, request):
        self.received_request = request

        if self.exception is not None:
            raise self.exception

        return self.response


class FakeInnerLogger:
    def exception(self, message):
        pass


class FakeLogger:
    logger = FakeInnerLogger()

    def log_info(self, message):
        pass

    def log_warning(self, message):
        pass


class AnalysisQueryControllerTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_success_payload(self):
        response_data = AnalysisQueryResponseDataDTO(
            dataset_id=DATASET_ID,
            executed_sql="select name from dataset",
            columns=["name"],
            rows=[{"name": "Ana"}],
            rows_count=1,
            returned_rows_count=1,
            limit=20,
        )
        service = FakeAnalysisService(response=response_data)
        controller = AnalysisQueryController(service, logger=FakeLogger())
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            sql="select name from dataset",
        )

        result = await controller.execute(request)

        self.assertIs(service.received_request, request)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Analysis query executed successfully.")
        self.assertIs(result.data, response_data)
        self.assertIsNone(result.errors)

    async def test_execute_maps_app_exception_to_http_exception(self):
        service = FakeAnalysisService(
            exception=AppException(
                message="Unsafe SQL query.",
                status_code=422,
                details=["Only read-only SELECT queries are allowed."],
            )
        )
        controller = AnalysisQueryController(service, logger=FakeLogger())
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            sql="delete from dataset",
        )

        with self.assertRaises(HTTPException) as context:
            await controller.execute(request)

        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(
            context.exception.detail,
            {
                "success": False,
                "message": "Unsafe SQL query.",
                "data": None,
                "errors": ["Only read-only SELECT queries are allowed."],
            },
        )

    async def test_execute_maps_unexpected_exception_to_internal_error(self):
        service = FakeAnalysisService(exception=RuntimeError("boom"))
        controller = AnalysisQueryController(service, logger=FakeLogger())
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            sql="select * from dataset",
        )

        with self.assertRaises(HTTPException) as context:
            await controller.execute(request)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            {
                "success": False,
                "message": (
                    "Internal server error during analysis query execution."
                ),
                "data": None,
                "errors": ["An unexpected internal error occurred."],
            },
        )


if __name__ == "__main__":
    unittest.main()
