from app.repositories.in_memory_upload_metadata_repository import (
    InMemoryUploadMetadataRepository,
)


def test_update_status_updates_existing_metadata() -> None:
    repository = InMemoryUploadMetadataRepository()
    metadata = {
        "dataset_id": "dataset-id",
        "upload_id": "upload-id",
        "upload_status": "UPLOADING",
        "dataset_status": "UPLOADING",
    }

    repository.create(metadata)
    repository.update_status(
        dataset_id="dataset-id",
        upload_id="upload-id",
        upload_status="COMPLETED",
        dataset_status="AVAILABLE",
    )

    stored_metadata = repository.find_by_dataset_and_upload(
        dataset_id="dataset-id",
        upload_id="upload-id",
    )

    assert stored_metadata["upload_status"] == "COMPLETED"
    assert stored_metadata["dataset_status"] == "AVAILABLE"


def test_update_status_ignores_missing_metadata() -> None:
    repository = InMemoryUploadMetadataRepository()

    repository.update_status(
        dataset_id="missing",
        upload_id="missing",
        upload_status="COMPLETED",
        dataset_status="AVAILABLE",
    )

    assert repository.storage == {}


def test_store_completed_parts_updates_existing_metadata() -> None:
    repository = InMemoryUploadMetadataRepository()
    metadata = {
        "dataset_id": "dataset-id",
        "upload_id": "upload-id",
    }
    parts = [{"part_number": 1, "etag": "etag"}]

    repository.create(metadata)
    repository.store_completed_parts(
        dataset_id="dataset-id",
        upload_id="upload-id",
        parts=parts,
    )

    stored_metadata = repository.find_by_dataset_and_upload(
        dataset_id="dataset-id",
        upload_id="upload-id",
    )

    assert stored_metadata["completed_parts"] == parts


def test_store_completed_parts_ignores_missing_metadata() -> None:
    repository = InMemoryUploadMetadataRepository()

    repository.store_completed_parts(
        dataset_id="missing",
        upload_id="missing",
        parts=[{"part_number": 1, "etag": "etag"}],
    )

    assert repository.storage == {}