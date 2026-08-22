import asyncio
import json
import unittest

from fastapi import HTTPException

from app.analysis.dependencies import get_analysis_query_controller
from app.main import app
from tests.helpers import DATASET_ID


class FakeAnalysisController:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_request = None

    async def execute(self, request):
        self.received_request = request

        if self.exception is not None:
            raise self.exception

        return self.response


def post(path: str, payload: dict):
    return asyncio.run(
        asyncio.wait_for(
            asgi_request("POST", path, payload),
            timeout=2,
        )
    )


async def asgi_request(method: str, path: str, payload: dict):
    messages = []
    request_sent = False
    body = json.dumps(payload).encode()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    async def receive():
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}

        request_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)

    response_start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )

    return response_start["status"], json.loads(response_body)


def make_analysis_response(limit=2):
    return {
        "success": True,
        "message": "Analysis query executed successfully.",
        "data": {
            "dataset_id": str(DATASET_ID),
            "executed_sql": "select name from dataset",
            "columns": ["name"],
            "rows": [{"name": "Ana"}],
            "rows_count": 1,
            "returned_rows_count": 1,
            "limit": limit,
        },
        "errors": None,
    }


class AnalysisQueryRouteTest(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def override_controller(self, controller: FakeAnalysisController):
        async def get_controller():
            return controller

        app.dependency_overrides[get_analysis_query_controller] = get_controller

    def test_execute_analysis_query_returns_success_response(self):
        expected_response = make_analysis_response(limit=2)
        controller = FakeAnalysisController(response=expected_response)
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/analysis/query",
            {
                "dataset_id": str(DATASET_ID),
                "sql": " select name from dataset ",
                "limit": 2,
            },
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_request.dataset_id, DATASET_ID)
        self.assertEqual(
            controller.received_request.sql,
            "select name from dataset",
        )
        self.assertEqual(controller.received_request.limit, 2)

    def test_execute_analysis_query_uses_default_limit(self):
        expected_response = make_analysis_response(limit=20)
        controller = FakeAnalysisController(response=expected_response)
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/analysis/query",
            {
                "dataset_id": str(DATASET_ID),
                "sql": "select name from dataset",
            },
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_request.limit, 20)

    def test_execute_analysis_query_rejects_invalid_dataset_id(self):
        controller = FakeAnalysisController()
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/analysis/query",
            {
                "dataset_id": "not-a-uuid",
                "sql": "select name from dataset",
            },
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["body", "dataset_id"])
        self.assertIsNone(controller.received_request)

    def test_execute_analysis_query_rejects_missing_query_input(self):
        controller = FakeAnalysisController()
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/analysis/query",
            {
                "dataset_id": str(DATASET_ID),
                "question": "   ",
                "sql": "   ",
            },
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["body"])
        self.assertIsNone(controller.received_request)

    def test_execute_analysis_query_rejects_limit_lower_than_one(self):
        controller = FakeAnalysisController()
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/analysis/query",
            {
                "dataset_id": str(DATASET_ID),
                "sql": "select name from dataset",
                "limit": 0,
            },
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["body", "limit"])
        self.assertIsNone(controller.received_request)

    def test_execute_analysis_query_rejects_limit_greater_than_one_hundred(self):
        controller = FakeAnalysisController()
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/analysis/query",
            {
                "dataset_id": str(DATASET_ID),
                "sql": "select name from dataset",
                "limit": 101,
            },
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["body", "limit"])
        self.assertIsNone(controller.received_request)

    def test_execute_analysis_query_returns_controller_http_exception_response(self):
        controller = FakeAnalysisController(
            exception=HTTPException(
                status_code=409,
                detail={
                    "success": False,
                    "message": (
                        "Dataset must be prepared or profiled before analysis."
                    ),
                    "data": None,
                    "errors": [],
                },
            )
        )
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/analysis/query",
            {
                "dataset_id": str(DATASET_ID),
                "sql": "select name from dataset",
            },
        )

        self.assertEqual(status_code, 409)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": (
                        "Dataset must be prepared or profiled before analysis."
                    ),
                    "data": None,
                    "errors": [],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
