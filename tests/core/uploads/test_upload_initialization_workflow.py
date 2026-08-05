import pytest

from app.adapters.storage.fake_blob_storage_adapter import FakeBlobStorageAdapter
from app.core.uploads.workflow import UploadInitializationWorkflow
from app.repositories.upload_metadata_repository import UploadMetadataRepository
from app.routes.uploads.dtos.dto import UploadInitRequestDTO
from app.settings.setting import UploadSettings


class MockUploadMetadataRepository(UploadMetadataRepository):
    def __init__(self) -> None:
        self.created_metadata = None

    async def create(self, metadata):
        self.created_metadata = metadata

    async def find_by_dataset_and_upload(self, dataset_id, upload_id):
        return self.created_metadata

    async def update_status(
        self,
        dataset_id,
        upload_id,
        upload_status,
        dataset_status,
    ):
        return None

    async def store_completed_parts(
        self,
        dataset_id,
        upload_id,
        parts,
    ):
        return None


def make_workflow():
    repository = MockUploadMetadataRepository()
    storage_adapter = FakeBlobStorageAdapter()

    config = UploadSettings(
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
    filename="customers.csv",
    content_type="text/csv",
    file_size_bytes=6_000_000,
    dataset_name=" Customers Dataset ",
):
    return UploadInitRequestDTO(
        filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        dataset_name=dataset_name,
        description="Test dataset",
    )


@pytest.mark.asyncio
async def test_run_initializes_upload_successfully():
    workflow, repository = make_workflow()

    result = await workflow.run(make_request())

    assert result["status"] == "UPLOADING"
    assert result["chunk_size_bytes"] == 5_000_000
    assert result["chunks_count"] == 2
    assert len(result["parts"]) == 2
    assert result["parts"][0].part_number == 1
    assert result["parts"][1].part_number == 2
    assert result["object_key"].endswith("/raw/customers.csv")

    assert repository.created_metadata is not None
    assert repository.created_metadata["dataset_name"] == "Customers Dataset"
    assert repository.created_metadata["upload_status"] == "UPLOADING"
    assert repository.created_metadata["dataset_status"] == "UPLOADING"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("customers.pdf", "application/pdf"),
        ("customers.json", "application/json"),
    ],
)
async def test_run_rejects_invalid_file_extension(
    filename,
    content_type,
):
    workflow, _ = make_workflow()

    with pytest.raises(ValueError, match="Invalid file extension"):
        await workflow.run(
            make_request(
                filename=filename,
                content_type=content_type,
            )
        )


@pytest.mark.asyncio
async def test_run_rejects_invalid_content_type():
    workflow, _ = make_workflow()

    with pytest.raises(ValueError, match="Invalid content type"):
        await workflow.run(
            make_request(
                filename="customers.csv",
                content_type="application/pdf",
            )
        )


@pytest.mark.asyncio
async def test_run_rejects_file_larger_than_configured_limit():
    workflow, _ = make_workflow()

    with pytest.raises(ValueError, match="File size exceeds"):
        await workflow.run(
            make_request(file_size_bytes=20_000_000)
        )


@pytest.mark.asyncio
async def test_run_accepts_xlsx_file():
    workflow, _ = make_workflow()

    result = await workflow.run(
        make_request(
            filename="customers.xlsx",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
    )

    assert result["status"] == "UPLOADING"
    assert result["object_key"].endswith("/raw/customers.xlsx")
