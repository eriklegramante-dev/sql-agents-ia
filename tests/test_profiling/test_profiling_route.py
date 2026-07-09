import asyncio
import json
import unittest
from uuid import UUID

from app.main import app
from app.prepare.exceptions import ConflictException, NotFoundException
from app.profiling.dependencies import get_dataset_profile_controller
from tests.helpers import DATASET_ID


class FakeProfileController:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_dataset_id = None

    async def profile_dataset(self, dataset_id: UUID) -> dict:
        self.received_dataset_id = dataset_id

        if self.exception is not None:
            raise self.exception

        return self.response


def post(path: str):
    return asyncio.run(asyncio.wait_for(asgi_request("POST", path), timeout=2))


async def asgi_request(method: str, path: str):
    messages = []
    request_sent = False

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
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


def make_profile_response():
    return {
        "success": True,
        "message": "Dataset profiled successfully.",
        "data": {
            "dataset_id": str(DATASET_ID),
            "status": "PROFILED",
            "rows_count": 2,
            "columns_count": 2,
            "columns": [
                {
                    "name": "amount",
                    "type": "numeric",
                    "nullable": False,
                    "null_count": 0,
                    "null_percentage": 0.0,
                    "cardinality": 2,
                    "statistics": {"mean": 15.25},
                }
            ],
            "nulls_summary": {
                "total_nulls": 0,
                "columns_with_nulls": 0,
            },
            "cardinality_summary": {
                "high_cardinality_columns": ["amount"],
                "low_cardinality_columns": [],
            },
            "basic_statistics": {"rows": 2},
            "quality_warnings": [],
            "updated_at": "2026-06-23T15:30:45",
        },
    }


class ProfileDatasetRouteTest(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def override_controller(self, controller: FakeProfileController):
        async def get_controller():
            return controller

        app.dependency_overrides[get_dataset_profile_controller] = get_controller

    def test_profile_dataset_returns_success_response(self):
        expected_response = make_profile_response()
        controller = FakeProfileController(response=expected_response)
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/profile")

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_dataset_id, DATASET_ID)

    def test_profile_dataset_rejects_invalid_uuid(self):
        self.override_controller(FakeProfileController())

        status_code, response_json = post("/api/v1/datasets/not-a-uuid/profile")

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["path", "dataset_id"])

    def test_profile_dataset_returns_not_found_when_dataset_does_not_exist(self):
        controller = FakeProfileController(exception=NotFoundException("Dataset not found."))
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/profile")

        self.assertEqual(status_code, 404)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "Dataset not found.",
                    "data": None,
                    "errors": [],
                }
            },
        )

    def test_profile_dataset_returns_conflict_when_dataset_is_not_prepared(self):
        controller = FakeProfileController(
            exception=ConflictException("Only prepared datasets can be profiled.")
        )
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/profile")

        self.assertEqual(status_code, 409)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "Only prepared datasets can be profiled.",
                    "data": None,
                    "errors": [],
                }
            },
        )

    def test_profile_dataset_returns_internal_error_on_generic_exception(self):
        controller = FakeProfileController(exception=RuntimeError("boom"))
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/profile")

        self.assertEqual(status_code, 500)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "Internal server error during dataset profiling",
                    "data": None,
                    "errors": ["boom"],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
