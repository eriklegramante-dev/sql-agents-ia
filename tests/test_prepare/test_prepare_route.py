import asyncio
import json
import unittest
from datetime import datetime
from uuid import UUID

from app.prepare.dependencies import get_dataset_preparation_controller
from app.prepare.exceptions import ConflictException, NotFoundException, StorageException
from app.main import app
from tests.helpers import DATASET_ID


class FakePreparationController:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_dataset_id = None

    async def prepare_dataset(self, dataset_id: UUID) -> dict:
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


class PrepareDatasetRouteTest(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def override_controller(self, controller: FakePreparationController):
        async def get_controller():
            return controller

        app.dependency_overrides[get_dataset_preparation_controller] = (
            get_controller
        )

    def test_prepare_dataset_returns_success_response(self):
        expected_response = {
            "success": True,
            "message": "Dataset prepared successfully",
            "data": {
                "dataset_id": str(DATASET_ID),
                "status": "prepared",
                "raw_object_key": "uploads/input.csv",
                "prepared_object_key": f"{DATASET_ID}/prepared.parquet",
                "rows_count": 2,
                "columns_count": 2,
                "schema": [
                    {
                        "name": "amount",
                        "type": "float",
                        "nullable": False,
                        "original_name": "Amount",
                    }
                ],
                "updated_at": datetime(2026, 6, 23, 12, 0, 0).isoformat(),
            },
            "errors": None,
        }
        controller = FakePreparationController(response=expected_response)
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/prepare")

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_dataset_id, DATASET_ID)

    def test_prepare_dataset_rejects_invalid_uuid(self):
        self.override_controller(FakePreparationController())

        status_code, response_json = post("/api/v1/datasets/not-a-uuid/prepare")

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["path", "dataset_id"])

    def test_prepare_dataset_returns_not_found_when_dataset_does_not_exist(self):
        controller = FakePreparationController(
            exception=NotFoundException(f"Dataset with ID {DATASET_ID} not found")
        )
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/prepare")

        self.assertEqual(status_code, 404)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": f"Dataset with ID {DATASET_ID} not found",
                    "data": None,
                    "errors": [],
                }
            },
        )

    def test_prepare_dataset_returns_conflict_when_dataset_is_already_prepared(self):
        controller = FakePreparationController(
            exception=ConflictException("Dataset already prepared")
        )
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/prepare")

        self.assertEqual(status_code, 409)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "Dataset already prepared",
                    "data": None,
                    "errors": [],
                }
            },
        )

    def test_prepare_dataset_returns_internal_error_on_storage_exception(self):
        controller = FakePreparationController(
            exception=StorageException("raw/uploads/input.csv not found")
        )
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/prepare")

        self.assertEqual(status_code, 500)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "raw/uploads/input.csv not found",
                    "data": None,
                    "errors": [],
                }
            },
        )

    def test_prepare_dataset_returns_internal_error_on_generic_exception(self):
        controller = FakePreparationController(exception=RuntimeError("boom"))
        self.override_controller(controller)

        status_code, response_json = post(f"/api/v1/datasets/{DATASET_ID}/prepare")

        self.assertEqual(status_code, 500)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "Internal server error during dataset preparation",
                    "data": None,
                    "errors": ["boom"],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
