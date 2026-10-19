import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.analysis.dependencies import get_analysis_query_controller
from app.main import app
from tests.helpers import DATASET_ID
from app.security.security import get_trusted_user_id, verify_signature

TEST_SIGNATURE = "analysis-test-signature"
VALID_HEADERS = {"X-Signature": TEST_SIGNATURE, "X-User-Id": "37"}


class FakeAnalysisController:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_request = None

    async def execute(self, request, *, user_id):
        self.received_request = request
        self.received_user_id = user_id

        if self.exception is not None:
            raise self.exception

        return self.response


def post(path: str, payload: dict, headers=None):
    return asyncio.run(
        asyncio.wait_for(
            asgi_request("POST", path, payload, VALID_HEADERS if headers is None else headers),
            timeout=2,
        )
    )


async def asgi_request(method: str, path: str, payload: dict, headers: dict):
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

    scope["headers"].extend(
        (name.lower().encode(), value.encode()) for name, value in headers.items()
    )

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
    def setUp(self):
        original_overrides = app.dependency_overrides.copy()

        def restore_overrides():
            app.dependency_overrides.clear()
            app.dependency_overrides.update(original_overrides)

        self.addCleanup(restore_overrides)
        app.dependency_overrides.pop(get_trusted_user_id, None)
        app.dependency_overrides.pop(verify_signature, None)
        settings_patch = patch(
            "app.security.security.get_settings",
            return_value=SimpleNamespace(security=SimpleNamespace(secret_key=TEST_SIGNATURE)),
        )
        settings_patch.start()
        self.addCleanup(settings_patch.stop)

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
        self.assertEqual(controller.received_user_id, 37)
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

    def test_security_rejects_headers_before_controller_execution(self):
        cases = [({}, 422), ({"X-User-Id": "37"}, 422),
                 ({"X-Signature": TEST_SIGNATURE}, 422),
                 ({"X-Signature": "incorrect", "X-User-Id": "37"}, 401)]
        cases.extend(({"X-Signature": TEST_SIGNATURE, "X-User-Id": value}, 422)
                     for value in ("", "abc", "0", "-1", "1.5", "true"))
        for headers, expected_status in cases:
            with self.subTest(headers=headers):
                controller = FakeAnalysisController()
                self.override_controller(controller)
                status_code, _ = post(
                    "/api/v1/analysis/query",
                    {"dataset_id": str(DATASET_ID), "sql": "SELECT * FROM dataset"},
                    headers=headers,
                )
                self.assertEqual(status_code, expected_status)
                self.assertIsNone(controller.received_request)

    def test_real_layers_enforce_ownership_and_preserve_not_found(self):
        from unittest.mock import AsyncMock, Mock
        from app.core.analysis.workflow import AnalysisQueryWorkflow
        from app.analysis.sql_safety_validator import SQLSafetyValidator
        from app.routes.analysis.controllers.controller import AnalysisQueryController
        from app.routes.analysis.services.service import AnalysisQueryService
        from app.adapters.analysis.duckdb_query_adapter import DuckDBQueryResult

        for owner, expected_status in ((37, 200), (23, 403), (None, 403), ("missing", 404)):
            with self.subTest(owner=owner):
                repository = Mock()
                repository.get_by_id = AsyncMock(return_value=(
                    None if owner == "missing" else SimpleNamespace(
                        user_id=owner, status="PREPARED",
                        prepared_object_key="datasets/prepared.parquet",
                    )
                ))
                storage = Mock(read_file=AsyncMock(return_value=b"fake-parquet"))
                executor = Mock()
                executor.execute.return_value = DuckDBQueryResult(
                    columns=["name"], rows=[{"name": "Ana"}],
                    rows_count=1, returned_rows_count=1,
                )
                logger = Mock()
                executions = Mock(record_success=AsyncMock())
                workflow = AnalysisQueryWorkflow(
                    repository, storage, SQLSafetyValidator(), executor, logger, executions,
                )
                controller = AnalysisQueryController(
                    AnalysisQueryService(workflow, logger), logger,
                )
                self.override_controller(controller)
                status_code, response = post(
                    "/api/v1/analysis/query",
                    {"dataset_id": str(DATASET_ID), "sql": "select name from dataset", "limit": 2},
                )
                self.assertEqual(status_code, expected_status)
                repository.get_by_id.assert_awaited_once_with(DATASET_ID)
                if expected_status == 200:
                    executions.record_success.assert_awaited_once_with(user_id=37, dataset_id=DATASET_ID)
                    self.assertEqual(response, make_analysis_response(limit=2))
                    storage.read_file.assert_awaited_once_with(
                        container="prepared", path="datasets/prepared.parquet",
                    )
                    executor.execute.assert_called_once_with(
                        parquet_content=b"fake-parquet", sql="select name from dataset", limit=2,
                    )
                else:
                    self.assertFalse(response["detail"]["success"])
                    storage.read_file.assert_not_awaited()
                    executor.execute.assert_not_called()
                    executions.record_success.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
