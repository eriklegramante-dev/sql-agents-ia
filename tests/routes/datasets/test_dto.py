from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.routes.datasets.dtos.dto import (
    DatasetRequestDTO,
    DatasetResponseDataDTO,
    DatasetResponseDTO,
)


def make_dataset_response_data() -> DatasetResponseDataDTO:
    return DatasetResponseDataDTO(
        dataset_id=UUID("12345678-1234-5678-1234-567812345678"),
        name="Customers Dataset",
        original_filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1024,
        status="UPLOADED",
        object_key="datasets/12345678/raw/customers.csv",
        description="Customer dataset.",
        created_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 8, 11, 12, 30, tzinfo=UTC),
    )


def test_dataset_request_dto_accepts_valid_uuid():
    dataset_id = uuid4()

    result = DatasetRequestDTO(dataset_id=dataset_id)

    assert result.dataset_id == dataset_id


def test_dataset_request_dto_rejects_invalid_uuid():
    with pytest.raises(ValidationError):
        DatasetRequestDTO(dataset_id="invalid-uuid")


def test_dataset_response_data_dto_accepts_valid_data():
    dataset_id = uuid4()

    result = DatasetResponseDataDTO(
        dataset_id=dataset_id,
        name="Customers Dataset",
        original_filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1024,
        status="UPLOADED",
        object_key="datasets/test/raw/customers.csv",
        description="Customer dataset.",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert result.dataset_id == dataset_id
    assert result.name == "Customers Dataset"
    assert result.original_filename == "customers.csv"
    assert result.content_type == "text/csv"
    assert result.file_size_bytes == 1024
    assert result.status == "UPLOADED"
    assert result.object_key == "datasets/test/raw/customers.csv"
    assert result.description == "Customer dataset."


def test_dataset_response_data_dto_accepts_optional_fields_as_none():
    result = DatasetResponseDataDTO(
        dataset_id=uuid4(),
        name="Customers Dataset",
        status="UPLOADED",
        object_key="datasets/test/raw/customers.csv",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert result.original_filename is None
    assert result.content_type is None
    assert result.file_size_bytes is None
    assert result.description is None


def test_dataset_response_dto_accepts_success_response():
    data = make_dataset_response_data()

    result = DatasetResponseDTO(
        success=True,
        message="Dataset retrieved successfully.",
        data=data,
    )

    assert result.success is True
    assert result.message == "Dataset retrieved successfully."
    assert result.data == data
    assert result.errors is None


def test_dataset_response_dto_accepts_error_response_without_data():
    result = DatasetResponseDTO(
        success=False,
        message="Dataset not found.",
        errors=["Dataset does not exist."],
    )

    assert result.success is False
    assert result.message == "Dataset not found."
    assert result.data is None
    assert result.errors == ["Dataset does not exist."]
