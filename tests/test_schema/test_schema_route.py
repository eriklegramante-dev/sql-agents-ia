import asyncio
import json
import unittest
from datetime import datetime
from uuid import UUID

from app.main import app
from app.prepare.exceptions import ConflictException, NotFoundException
from app.routes.schema.dependencies.dependence import get_dataset_schema_controller
from tests.helpers import DATASET_ID


class FakeSchemaController:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_dataset_id = None

    async def get_dataset_schema(self, dataset_id: UUID) -> dict:
        self.received_dataset_id = dataset_id

        if self.exception is not None:
            raise self.exception

        return self.response


def get(path: str):
    return asyncio.run(asyncio.wait_for(asgi_request("GET", path), timeout=2))


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


class DatasetSchemaRouteTest(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def override_controller(self, controller: FakeSchemaController):
        async def get_controller():
            return controller

        app.dependency_overrides[get_dataset_schema_controller] = get_controller

    def test_get_dataset_schema_returns_success_response(self):
        expected_response = {
            "success": True,
            "message": "Dataset schema retrieved successfully.",
            "data": {
                "dataset_id": str(DATASET_ID),
                "status": "PREPARED",
                "columns_count": 1,
                "schema": [
                    {
                        "name": "amount",
                        "original_name": "Amount",
                        "type": "numeric",
                        "nullable": False,
                        "sample_values": ["10", "20"],
                        "warnings": [],
                    }
                ],
                "updated_at": datetime(2026, 6, 23, 12, 0, 0).isoformat(),
            },
            "errors": None,
        }
        controller = FakeSchemaController(response=expected_response)
        self.override_controller(controller)

        status_code, response_json = get(f"/api/v1/datasets/{DATASET_ID}/schema")

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_dataset_id, DATASET_ID)

    def test_get_dataset_schema_rejects_invalid_uuid(self):
        self.override_controller(FakeSchemaController())

        status_code, response_json = get("/api/v1/datasets/not-a-uuid/schema")

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["path", "dataset_id"])

    def test_get_dataset_schema_returns_not_found_when_dataset_does_not_exist(self):
        controller = FakeSchemaController(
            exception=NotFoundException(f"Dataset with ID {DATASET_ID} not found.")
        )
        self.override_controller(controller)

        status_code, response_json = get(f"/api/v1/datasets/{DATASET_ID}/schema")

        self.assertEqual(status_code, 404)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": f"Dataset with ID {DATASET_ID} not found.",
                    "data": None,
                    "errors": [],
                }
            },
        )

    def test_get_dataset_schema_returns_conflict_when_dataset_is_not_prepared(self):
        controller = FakeSchemaController(
            exception=ConflictException(
                "Dataset schema is not available yet. Please prepare the dataset first."
            )
        )
        self.override_controller(controller)

        status_code, response_json = get(f"/api/v1/datasets/{DATASET_ID}/schema")

        self.assertEqual(status_code, 409)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "Dataset schema is not available yet. Please prepare the dataset first.",
                    "data": None,
                    "errors": [],
                }
            },
        )

    def test_get_dataset_schema_returns_internal_error_on_generic_exception(self):
        controller = FakeSchemaController(exception=RuntimeError("boom"))
        self.override_controller(controller)

        status_code, response_json = get(f"/api/v1/datasets/{DATASET_ID}/schema")

        self.assertEqual(status_code, 500)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "Internal server error during dataset schema retrieval",
                    "data": None,
                    "errors": ["boom"],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
