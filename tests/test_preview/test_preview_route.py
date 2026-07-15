import asyncio
import json
import unittest

from app.main import app
from app.prepare.exceptions import AppException
from app.preview.dependencies import get_dataset_preview_controller
from tests.helpers import DATASET_ID


class FakePreviewController:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_request = None

    async def execute(self, request):
        self.received_request = request

        if self.exception is not None:
            raise self.exception

        return self.response


def get(path: str):
    return asyncio.run(asyncio.wait_for(asgi_request("GET", path), timeout=2))


async def asgi_request(method: str, path: str):
    messages = []
    request_sent = False
    route_path, _, query_string = path.partition("?")

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": route_path,
        "raw_path": route_path.encode(),
        "query_string": query_string.encode(),
        "headers": [(b"host", b"testserver")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    async def receive():
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}

        request_sent = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)

    response_start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )

    return response_start["status"], json.loads(body)


def make_preview_response(limit=2):
    return {
        "success": True,
        "message": "Dataset preview retrieved successfully.",
        "data": {
            "dataset_id": str(DATASET_ID),
            "status": "PREPARED",
            "limit": limit,
            "columns": ["name", "age"],
            "rows": [{"name": "Ana", "age": 30}],
            "rows_count": 1,
            "returned_rows_count": 1,
        },
        "errors": None,
    }


class DatasetPreviewRouteTest(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def override_controller(self, controller: FakePreviewController):
        async def get_controller():
            return controller

        app.dependency_overrides[get_dataset_preview_controller] = get_controller

    def test_get_dataset_preview_returns_success_response(self):
        expected_response = make_preview_response(limit=2)
        controller = FakePreviewController(response=expected_response)
        self.override_controller(controller)

        status_code, response_json = get(
            f"/api/v1/datasets/{DATASET_ID}/preview?limit=2"
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_request.dataset_id, DATASET_ID)
        self.assertEqual(controller.received_request.limit, 2)

    def test_get_dataset_preview_uses_default_limit(self):
        expected_response = make_preview_response(limit=20)
        controller = FakePreviewController(response=expected_response)
        self.override_controller(controller)

        status_code, response_json = get(f"/api/v1/datasets/{DATASET_ID}/preview")

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_request.limit, 20)

    def test_get_dataset_preview_rejects_invalid_uuid(self):
        self.override_controller(FakePreviewController())

        status_code, response_json = get("/api/v1/datasets/not-a-uuid/preview")

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["path", "dataset_id"])

    def test_get_dataset_preview_rejects_invalid_limit(self):
        self.override_controller(FakePreviewController())

        status_code, response_json = get(
            f"/api/v1/datasets/{DATASET_ID}/preview?limit=0"
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["query", "limit"])

    def test_get_dataset_preview_returns_app_exception_response(self):
        controller = FakePreviewController(
            exception=AppException(
                message="Dataset must be prepared or profiled before preview retrieval.",
                status_code=409,
            )
        )
        self.override_controller(controller)

        status_code, response_json = get(f"/api/v1/datasets/{DATASET_ID}/preview")

        self.assertEqual(status_code, 409)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": (
                        "Dataset must be prepared or profiled before preview "
                        "retrieval."
                    ),
                    "data": None,
                    "errors": [],
                }
            },
        )

    def test_get_dataset_preview_returns_internal_error_on_generic_exception(self):
        controller = FakePreviewController(exception=RuntimeError("boom"))
        self.override_controller(controller)

        status_code, response_json = get(f"/api/v1/datasets/{DATASET_ID}/preview")

        self.assertEqual(status_code, 500)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": (
                        "Internal server error during dataset preview retrieval."
                    ),
                    "data": None,
                    "errors": ["boom"],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
