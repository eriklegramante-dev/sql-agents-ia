from datetime import datetime
from uuid import UUID, uuid4

from app.main import app
from app.routes.datasets.dependencies.dependence import (
    get_dataset_controller,
)


class FakeDatasetController:
    async def get_dataset(
        self,
        dataset_id: UUID,
    ):
        now = datetime.now()

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


def test_get_dataset_route_success(client):
    app.dependency_overrides[get_dataset_controller] = lambda: FakeDatasetController()

    dataset_id = uuid4()

    try:
        response = client.get(f"/api/v1/datasets/{dataset_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == "Dataset retrieved successfully."

    assert body["data"]["dataset_id"] == str(dataset_id)

    assert body["data"]["status"] == "COMPLETED"


def test_get_dataset_route_rejects_invalid_uuid(client):
    app.dependency_overrides[get_dataset_controller] = lambda: FakeDatasetController()

    try:
        response = client.get("/api/v1/datasets/invalid-uuid")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
