import pytest

from app.adapters.storage.fake_blob_storage_adapter import FakeBlobStorageAdapter
from app.core.uploads.dto import UploadInitRequestDTO
from app.core.uploads.init_workflow import UploadInitializationWorkflow
from app.repositories.in_memory_upload_metadata_repository import (
    InMemoryUploadMetadataRepository,
)
from app.settings.app_config import AppConfig


def make_workflow() -> tuple[
    UploadInitializationWorkflow,
    InMemoryUploadMetadataRepository,
]:
    repository = InMemoryUploadMetadataRepository()
    storage_adapter = FakeBlobStorageAdapter()
    config = AppConfig(
        max_upload_size_bytes=10_000_000,
        upload_chunk_size_bytes=5_000_000,
        signed_url_expires_seconds=3600,
    )
    workflow = UploadInitializationWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
        config=config,
    )
    return workflow, repository


def make_request(
    filename: str = "customers.csv",
    content_type: str = "text/csv",
    file_size_bytes: int = 6_000_000,
    dataset_name: str = " Customers Dataset ",
) -> UploadInitRequestDTO:
    return UploadInitRequestDTO(
        filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        dataset_name=dataset_name,
        description="Test dataset",
    )


def test_run_initializes_upload_successfully() -> None:
    workflow, repository = make_workflow()
    request = make_request()

    result = workflow.run(request)

    assert result["status"] == "UPLOADING"
    assert result["chunk_size_bytes"] == 5_000_000
    assert result["chunks_count"] == 2
    assert len(result["parts"]) == 2
    assert result["parts"][0].part_number == 1
    assert result["parts"][1].part_number == 2
    assert result["object_key"].endswith("/raw/customers.csv")

    metadata = repository.find_by_dataset_and_upload(
        dataset_id=str(result["dataset_id"]),
        upload_id=result["upload_id"],
    )

    assert metadata is not None
    assert metadata["dataset_name"] == "Customers Dataset"
    assert metadata["upload_status"] == "UPLOADING"
    assert metadata["dataset_status"] == "UPLOADING"


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("customers.pdf", "application/pdf"),
        ("customers.json", "application/json"),
    ],
)
def test_run_rejects_invalid_file_extension(
    filename: str,
    content_type: str,
) -> None:
    workflow, _ = make_workflow()
    request = make_request(filename=filename, content_type=content_type)

    with pytest.raises(ValueError, match="Invalid file extension"):
        workflow.run(request)


def test_run_rejects_invalid_content_type() -> None:
    workflow, _ = make_workflow()
    request = make_request(
        filename="customers.csv",
        content_type="application/pdf",
    )

    with pytest.raises(ValueError, match="Invalid content type"):
        workflow.run(request)


def test_run_rejects_file_larger_than_configured_limit() -> None:
    workflow, _ = make_workflow()
    request = make_request(file_size_bytes=20_000_000)

    with pytest.raises(ValueError, match="File size exceeds"):
        workflow.run(request)


def test_run_accepts_xlsx_file() -> None:
    workflow, _ = make_workflow()
    request = make_request(
        filename="customers.xlsx",
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

    result = workflow.run(request)

    assert result["status"] == "UPLOADING"
    assert result["object_key"].endswith("/raw/customers.xlsx")