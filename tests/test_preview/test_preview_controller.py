import unittest

from fastapi import HTTPException

from app.prepare.exceptions import AppException
from app.routes.preview.controllers.controller import DatasetPreviewController
from app.routes.preview.dtos.dto import (
    DatasetPreviewRequestDTO,
    DatasetPreviewResponseDataDTO,
)
from tests.helpers import DATASET_ID


class FakePreviewService:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_request = None

    async def execute(self, request):
        self.received_request = request

        if self.exception is not None:
            raise self.exception

        return self.response


class DatasetPreviewControllerTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_success_payload(self):
        response_data = DatasetPreviewResponseDataDTO(
            dataset_id=DATASET_ID,
            status="PREPARED",
            limit=2,
            columns=["name", "age"],
            rows=[{"name": "Ana", "age": 30}],
            rows_count=1,
            returned_rows_count=1,
        )
        service = FakePreviewService(response=response_data)
        controller = DatasetPreviewController(service)
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=2,
        )

        result = await controller.execute(request)

        self.assertIs(service.received_request, request)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Dataset preview retrieved successfully.")
        self.assertIs(result.data, response_data)
        self.assertIsNone(result.errors)

    async def test_execute_maps_app_exception_to_http_exception(self):
        service = FakePreviewService(
            exception=AppException(
                message="Dataset not available.",
                status_code=409,
                details=["Prepare the dataset first."],
            )
        )
        controller = DatasetPreviewController(service)
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=2,
        )

        with self.assertRaises(HTTPException) as context:
            await controller.execute(request)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            context.exception.detail,
            {
                "success": False,
                "message": "Dataset not available.",
                "data": None,
                "errors": ["Prepare the dataset first."],
            },
        )

    async def test_execute_maps_unexpected_exception_to_internal_error(self):
        service = FakePreviewService(exception=RuntimeError("boom"))
        controller = DatasetPreviewController(service)
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=2,
        )

        with self.assertRaises(HTTPException) as context:
            await controller.execute(request)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            {
                "success": False,
                "message": (
                    "Internal server error during dataset preview retrieval."
                ),
                "data": None,
                "errors": ["boom"],
            },
        )


if __name__ == "__main__":
    unittest.main()
