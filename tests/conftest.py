import pytest

from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.main import app
from app.routes.uploads.dependencies.dependence import (
    get_upload_controller,
)


MAX_UPLOAD_SIZE = 100 * 1024 * 1024


class FakeUploadController:
    """
    Fake controller used for upload route tests.

    It simulates the upload controller behavior without using:
    - PostgreSQL
    - MinIO
    - external storage services
    """

    async def initialize_upload(self, request):

        filename = request.filename.lower()

        allowed_extensions = (
            ".csv",
            ".xlsx",
        )

        allowed_content_types = {
            "text/csv",
            "application/csv",
            "application/vnd.ms-excel",
            (
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
        }

        if not filename.endswith(allowed_extensions):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": (
                        "Invalid file extension. "
                        "Allowed: csv, xlsx."
                    ),
                    "data": None,
                },
            )

        if request.content_type not in allowed_content_types:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": (
                        "Invalid content type for upload."
                    ),
                    "data": None,
                },
            )

        if request.file_size_bytes > MAX_UPLOAD_SIZE:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": (
                        "File size exceeds limit."
                    ),
                    "data": None,
                },
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": (
                    "Upload initialized successfully."
                ),
                "data": {
                    "dataset_id": (
                        "3fa85f64-5717-4562-b3fc-2c963f66afa6"
                    ),
                    "upload_id": "fake-upload-id",
                    "object_key": (
                        "datasets/id/raw/customers.csv"
                    ),
                    "status": "UPLOADING",
                    "chunk_size_bytes": 5242880,
                    "chunks_count": 1,
                    "parts": [
                        {
                            "part_number": 1,
                            "upload_url": (
                                "https://fake-storage.local/upload"
                            ),
                        }
                    ],
                },
            },
        )

    async def complete_upload(self, request):

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": (
                    "Upload completed successfully."
                ),
                "data": {
                    "dataset_id": str(request.dataset_id),
                    "upload_id": request.upload_id,
                    "status": "COMPLETED",
                    "object_key": (
                        "datasets/dataset-1/raw/file.csv"
                    ),
                    "completed_parts_count": len(request.parts),
                },
            },
        )

    async def abort_upload(self, request):

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": (
                    "Upload abort processed successfully."
                ),
                "data": {
                    "dataset_id": str(request.dataset_id),
                    "upload_id": request.upload_id,
                    "upload_status": "ABORTED",
                    "dataset_status": "ABORTED",
                },
            },
        )


async def override_get_upload_controller():

    return FakeUploadController()


@pytest.fixture
def client():

    app.dependency_overrides[get_upload_controller] = (
        override_get_upload_controller
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()