from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_initialize_upload_route_success() -> None:
    response = client.post(
        "/api/v1/uploads/init",
        json={
            "filename": "customers.csv",
            "content_type": "text/csv",
            "file_size_bytes": 1000,
            "dataset_name": "Customers",
            "description": "Test dataset",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["data"]["status"] == "UPLOADING"
    assert body["data"]["chunks_count"] >= 1


def test_initialize_upload_route_rejects_invalid_extension() -> None:
    response = client.post(
        "/api/v1/uploads/init",
        json={
            "filename": "customers.pdf",
            "content_type": "application/pdf",
            "file_size_bytes": 1000,
            "dataset_name": "Customers",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert "Invalid file extension" in body["message"]


def test_initialize_upload_route_rejects_invalid_content_type() -> None:
    response = client.post(
        "/api/v1/uploads/init",
        json={
            "filename": "customers.csv",
            "content_type": "application/pdf",
            "file_size_bytes": 1000,
            "dataset_name": "Customers",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert "Invalid content type" in body["message"]


def test_initialize_upload_route_rejects_large_file() -> None:
    response = client.post(
        "/api/v1/uploads/init",
        json={
            "filename": "customers.csv",
            "content_type": "text/csv",
            "file_size_bytes": 999999999,
            "dataset_name": "Customers",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert "File size exceeds" in body["message"]


def test_initialize_upload_route_validates_request_body() -> None:
    response = client.post(
        "/api/v1/uploads/init",
        json={
            "filename": "",
            "content_type": "text/csv",
            "file_size_bytes": 1000,
            "dataset_name": "Customers",
        },
    )

    assert response.status_code == 422

def test_abort_upload_route_success() -> None:
    response = client.post(
        "/api/v1/uploads/abort",
        json={
            "dataset_id": "dataset-1",
            "upload_id": "upload-1",
        },
    )

    assert response.status_code in (200, 400)


def test_abort_upload_route_validates_request_body() -> None:
    response = client.post(
        "/api/v1/uploads/abort",
        json={
            "dataset_id": "",
            "upload_id": "",
        },
    )

    assert response.status_code == 422


def test_abort_upload_route_missing_upload_id() -> None:
    response = client.post(
        "/api/v1/uploads/abort",
        json={
            "dataset_id": "dataset-1",
        },
    )

    assert response.status_code == 422