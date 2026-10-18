from fastapi import status
from fastapi.responses import JSONResponse

from app.main import app
from app.routes.uploads.dependencies.dependence import (
    get_upload_controller,
)

UPLOAD_HEADERS = {
    "X-Signature": "dummy_secret_token",
    "X-User-Id": "17",
}

def test_initialize_upload_route_success(client) -> None:
    response = client.post(
        "/api/v1/uploads/init",
        headers=UPLOAD_HEADERS,
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


def test_initialize_upload_route_rejects_invalid_extension(client) -> None:
    response = client.post(
        "/api/v1/uploads/init",
        headers=UPLOAD_HEADERS,
        json={
            "filename": "customers.pdf",
            "content_type": "application/pdf",
            "file_size_bytes": 1000,
            "dataset_name": "Customers",
        },
    )

    assert response.status_code == 400


def test_initialize_upload_route_rejects_invalid_content_type(client) -> None:
    response = client.post(
        "/api/v1/uploads/init",
        headers=UPLOAD_HEADERS,
        json={
            "filename": "customers.csv",
            "content_type": "application/pdf",
            "file_size_bytes": 1000,
            "dataset_name": "Customers",
        },
    )

    assert response.status_code == 400


def test_initialize_upload_route_rejects_large_file(client) -> None:
    response = client.post(
        "/api/v1/uploads/init",
        headers=UPLOAD_HEADERS,
        json={
            "filename": "customers.csv",
            "content_type": "text/csv",
            "file_size_bytes": 999999999,
            "dataset_name": "Customers",
        },
    )

    assert response.status_code == 400


def test_initialize_upload_route_validates_request_body(client) -> None:
    response = client.post(
        "/api/v1/uploads/init",
        headers=UPLOAD_HEADERS,
        json={
            "filename": "",
            "content_type": "text/csv",
            "file_size_bytes": 1000,
            "dataset_name": "Customers",
        },
    )

    assert response.status_code == 422


def test_abort_upload_route_success(client) -> None:
    response = client.post(
        "/api/v1/uploads/abort",
        headers=UPLOAD_HEADERS,
        json={
            "dataset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "upload_id": "upload-1",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["upload_status"] == "ABORTED"


def test_abort_upload_route_validates_request_body(client) -> None:
    response = client.post(
        "/api/v1/uploads/abort",
        headers=UPLOAD_HEADERS,
        json={
            "dataset_id": "",
            "upload_id": "",
        },
    )

    assert response.status_code == 422


def test_abort_upload_route_missing_upload_id(client) -> None:
    response = client.post(
        "/api/v1/uploads/abort",
        headers=UPLOAD_HEADERS,
        json={
            "dataset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
    )

    assert response.status_code == 422


def test_complete_upload_route_success(client) -> None:

    class FakeUploadController:

        async def complete_upload(self, request,* , user_id: int):
            assert user_id == 17
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Upload completed successfully.",
                    "data": {
                        "dataset_id": str(request.dataset_id),
                        "upload_id": request.upload_id,
                        "status": "COMPLETED",
                        "object_key": f"datasets/{request.dataset_id}/raw/file.csv",
                        "completed_parts_count": len(request.parts),
                    },
                },
            )

    app.dependency_overrides[get_upload_controller] = lambda: FakeUploadController()

    try:
        response = client.post(
            "/api/v1/uploads/complete",
            headers=UPLOAD_HEADERS,
            json={
                "dataset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "upload_id": "upload-1",
                "parts": [
                    {
                        "part_number": 1,
                        "etag": "etag-1",
                    }
                ],
            },
        )

    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200


def test_complete_upload_route_rejects_empty_parts(client) -> None:
    response = client.post(
        "/api/v1/uploads/complete",
        headers=UPLOAD_HEADERS,
        json={
            "dataset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "upload_id": "upload-1",
            "parts": [],
        },
    )

    assert response.status_code == 422


def test_complete_upload_route_rejects_invalid_part_number(client) -> None:
    response = client.post(
        "/api/v1/uploads/complete",
        headers=UPLOAD_HEADERS,
        json={
            "dataset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "upload_id": "upload-1",
            "parts": [
                {
                    "part_number": 0,
                    "etag": "etag-1",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_complete_upload_route_rejects_blank_etag(client) -> None:
    response = client.post(
        "/api/v1/uploads/complete",
        headers=UPLOAD_HEADERS,
        json={
            "dataset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "upload_id": "upload-1",
            "parts": [
                {
                    "part_number": 1,
                    "etag": "   ",
                }
            ],
        },
    )

    assert response.status_code == 422
