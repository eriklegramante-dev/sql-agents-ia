"""HTTP listing tests with real security and application layers."""
from dataclasses import asdict
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.datasets.models import DatasetMetadata
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.dependencies import dependence
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO
from app.security import security

SECRET = "dataset-test-secret"
HEADERS = {"X-Signature": SECRET, "X-User-Id": "37"}


class FakeListRepository:
    def __init__(self):
        self.datasets = []
        self.calls = []

    async def list_metadata(self, *, user_id: int):
        self.calls.append(user_id)
        return self.datasets


@pytest.fixture
def listing_client(monkeypatch):
    """Replace external storage, DB and settings; preserve real security."""
    repository = FakeListRepository()
    settings = SimpleNamespace(
        security=SimpleNamespace(secret_key=SECRET),
        minio=SimpleNamespace(bucket_name="test-bucket"),
    )
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    monkeypatch.setattr(dependence, "get_settings", lambda: settings)
    monkeypatch.setattr(dependence, "get_dataset_repository", AsyncMock(return_value=repository))
    monkeypatch.setattr(dependence, "get_dataset_storage", lambda: object())
    listing = AsyncMock(wraps=DatasetController.list_datasets)

    async def spy(self, *, user_id: int):
        return await listing(self, user_id=user_id)

    monkeypatch.setattr(DatasetController, "list_datasets", spy)
    overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()
    try:
        with TestClient(app) as client:
            yield client, repository, listing
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)


@pytest.mark.parametrize("empty", [False, True])
def test_list_forwards_identity_and_preserves_response(listing_client, empty):
    client, repository, listing = listing_client
    now = datetime(2026, 1, 2, tzinfo=UTC)
    metadata = DatasetMetadata(
        dataset_id=UUID("11111111-1111-1111-1111-111111111111"),
        name="Customers", original_filename="customers.csv", content_type="text/csv",
        file_size_bytes=1024, status="COMPLETED", object_key="datasets/customers.csv",
        description="Test dataset", rows_count=12, columns_count=3, profile=None,
        created_at=now, updated_at=now,
    )
    repository.datasets = [] if empty else [metadata]
    response = client.get("/api/v1/datasets", headers=HEADERS)
    assert response.status_code == 200
    expected = [] if empty else [DatasetResponseDataDTO(**asdict(metadata)).model_dump(mode="json")]
    assert response.json() == {
        "success": True, "message": "Datasets retrieved successfully.",
        "data": expected, "errors": None,
    }
    assert repository.calls == [37]
    assert listing.await_count == 1
    assert listing.await_args.kwargs == {"user_id": 37}


@pytest.mark.parametrize("headers, status_code, field", [
    ({}, 422, "x-signature"),
    ({"X-User-Id": "37"}, 422, "x-signature"),
    ({"X-Signature": SECRET}, 422, "x-user-id"),
    ({**HEADERS, "X-User-Id": "abc"}, 422, "x-user-id"),
    ({**HEADERS, "X-User-Id": "0"}, 422, "x-user-id"),
    ({**HEADERS, "X-User-Id": "-1"}, 422, "x-user-id"),
    ({**HEADERS, "X-User-Id": "1.5"}, 422, "x-user-id"),
    ({**HEADERS, "X-User-Id": ""}, 422, "x-user-id"),
    ({**HEADERS, "X-Signature": "incorrect"}, 401, None),
])
def test_rejected_headers_do_not_call_listing(listing_client, headers, status_code, field):
    client, repository, listing = listing_client
    response = client.get("/api/v1/datasets", headers=headers)
    assert response.status_code == status_code
    if field:
        assert any(error["loc"][0] == "header" and error["loc"][1].lower() == field
                   for error in response.json()["detail"])
    else:
        assert response.json() == {"detail": "Invalid signature"}
    listing.assert_not_called()
    assert repository.calls == []
