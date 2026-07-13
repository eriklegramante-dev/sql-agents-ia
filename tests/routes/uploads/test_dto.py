import pytest
from pydantic import ValidationError

from app.routes.uploads.dtos.dto import UploadInitRequestDTO


def test_upload_init_request_rejects_blank_dataset_name() -> None:
    with pytest.raises(ValidationError):
        UploadInitRequestDTO(
            filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1000,
            dataset_name="   ",
            description=None,
        )

from app.routes.uploads.dtos.dto import (
    UploadAbortRequestDTO,
    UploadCompleteRequestDTO,
    UploadCompleteResponseDTO,
    UploadAbortResponseDTO,
    UploadAbortResponseDataDTO,
)


def test_upload_abort_request_accepts_valid_values() -> None:
    request = UploadAbortRequestDTO(
        dataset_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        upload_id="fake-upload-id",
    )

    assert str(request.dataset_id) == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    assert request.upload_id == "fake-upload-id"


def test_upload_abort_request_rejects_blank_upload_id() -> None:
    with pytest.raises(ValidationError):
        UploadAbortRequestDTO(
            dataset_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            upload_id="",
        )


def test_upload_abort_response_builds_successfully() -> None:
    response = UploadAbortResponseDTO(
        success=True,
        message="Upload abort processed successfully.",
        data=UploadAbortResponseDataDTO(
            dataset_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            upload_id="fake-upload-id",
            upload_status="ABORTED",
            dataset_status="ABORTED",
        ),
    )

    assert response.success is True
    assert response.data.upload_status == "ABORTED"
    assert response.data.dataset_status == "ABORTED"

def test_upload_complete_request_dto_accepts_valid_payload() -> None:
    request = UploadCompleteRequestDTO(
        dataset_id="dataset-1",
        upload_id="upload-1",
        parts=[
            {
                "part_number": 1,
                "etag": "etag-1",
            },
        ],
    )

    assert request.dataset_id == "dataset-1"
    assert request.upload_id == "upload-1"
    assert request.parts[0].part_number == 1
    assert request.parts[0].etag == "etag-1"


def test_upload_complete_response_dto_accepts_valid_payload() -> None:
    response = UploadCompleteResponseDTO(
        success=True,
        message="Upload completed successfully.",
        data={
            "dataset_id": "dataset-1",
            "upload_id": "upload-1",
            "status": "COMPLETED",
            "object_key": "datasets/dataset-1/raw/file.csv",
            "completed_parts_count": 1,
        },
    )

    assert response.success is True
    assert response.data.status == "COMPLETED"
    assert response.data.completed_parts_count == 1
