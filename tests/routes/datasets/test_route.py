from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.main import app
from app.prepare.exceptions import NotFoundException
from app.routes.datasets.dependencies.dependence import (
    get_dataset_controller,
)


class FakeDatasetController:
    """Fake dataset controller used by route tests."""

    def __init__(self) -> None:
        self.error: Exception | None = None

    async def get_dataset(
        self,
        dataset_id: UUID,
        *,
        user_id: int,
    ):
        """Return dataset metadata or raise the configured application error."""
        if self.error is not None:
            raise self.error

        now = datetime.now(UTC)

        return {
            "success": True,
            "message": "Dataset retrieved successfully.",
            "data": {
                "dataset_id": str(dataset_id),
                "name": "Customers",
                "original_filename": "customers.csv",
                "content_type": "text/csv",
                "file_size_bytes": 1024,
                "status": "COMPLETED",
                "object_key": "datasets/customers.csv",
                "description": "Dataset for tests",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
        }

    async def delete_dataset(
        self,
        dataset_id: UUID,
        *,
        user_id: int,
    ):
        """Return deletion data or raise the configured application error."""
        if self.error is not None:
            raise self.error

        now = datetime.now(UTC)

        return {
            "success": True,
            "message": "Dataset deleted successfully.",
            "data": {
                "dataset_id": str(dataset_id),
                "status": "DELETED",
                "updated_at": now.isoformat(),
            },
        }


def test_get_dataset_route_success(client):
    """Return dataset metadata for a valid retrieval request."""
    app.dependency_overrides[get_dataset_controller] = lambda: FakeDatasetController()

    dataset_id = uuid4()

    try:
        response = client.get(f"/api/v1/datasets/{dataset_id}", headers={"X-User-Id": "17", "X-Signature": "dummy_secret_token"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Dataset retrieved successfully."
    assert body["data"]["dataset_id"] == str(dataset_id)
    assert body["data"]["status"] == "COMPLETED"


def test_get_dataset_route_rejects_invalid_uuid(client):
    """Reject retrieval requests with an invalid dataset identifier."""
    app.dependency_overrides[get_dataset_controller] = lambda: FakeDatasetController()

    try:
        response = client.get("/api/v1/datasets/invalid-uuid", headers={"X-User-Id": "17", "X-Signature": "dummy_secret_token"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_get_dataset_route_handles_not_found_error(client):
    """Convert a retrieval application error into an HTTP response."""
    controller = FakeDatasetController()
    controller.error = NotFoundException("Dataset not found.")

    app.dependency_overrides[get_dataset_controller] = lambda: controller

    try:
        response = client.get(f"/api/v1/datasets/{uuid4()}", headers={"X-User-Id": "17", "X-Signature": "dummy_secret_token"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

    body = response.json()

    assert body["detail"]["success"] is False
    assert body["detail"]["message"] == "Dataset not found."
    assert body["detail"]["data"] is None


def test_delete_dataset_route_success(client):
    """Return the deleted dataset state for a valid deletion request."""
    app.dependency_overrides[get_dataset_controller] = lambda: FakeDatasetController()

    dataset_id = uuid4()

    try:
        response = client.delete(f"/api/v1/datasets/{dataset_id}", headers={"X-User-Id": "17", "X-Signature": "dummy_secret_token"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Dataset deleted successfully."
    assert body["data"]["dataset_id"] == str(dataset_id)
    assert body["data"]["status"] == "DELETED"
    assert body["data"]["updated_at"] is not None


def test_delete_dataset_route_rejects_invalid_uuid(client):
    """Reject deletion requests with an invalid dataset identifier."""
    app.dependency_overrides[get_dataset_controller] = lambda: FakeDatasetController()

    try:
        response = client.delete("/api/v1/datasets/invalid-uuid", headers={"X-User-Id": "17", "X-Signature": "dummy_secret_token"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_delete_dataset_route_handles_not_found_error(client):
    """Convert a deletion application error into an HTTP response."""
    controller = FakeDatasetController()
    controller.error = NotFoundException("Dataset not found.")

    app.dependency_overrides[get_dataset_controller] = lambda: controller

    try:
        response = client.delete(f"/api/v1/datasets/{uuid4()}", headers={"X-User-Id": "17", "X-Signature": "dummy_secret_token"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

    body = response.json()

    assert body["detail"]["success"] is False
    assert body["detail"]["message"] == "Dataset not found."
    assert body["detail"]["data"] is None
