import pytest
from minio.error import S3Error

from app.adapters.storage.minio_blob_storage_adapter import (
    MinioBlobStorageAdapter,
)


class FakeMinioClient:
    def __init__(self, bucket_exists: bool = True) -> None:
        self.bucket_exists_result = bucket_exists
        self.created_bucket = None
        self.aborted_upload = None
        self.completed_upload = None

    def bucket_exists(self, bucket_name: str) -> bool:
        return self.bucket_exists_result

    def make_bucket(self, bucket_name: str) -> None:
        self.created_bucket = bucket_name

    def _create_multipart_upload(
        self,
        bucket_name: str,
        object_name: str,
        headers: dict[str, str],
    ) -> str:
        return "upload-id"

    def get_presigned_url(
        self,
        method: str,
        bucket_name: str,
        object_name: str,
        expires,
        extra_query_params: dict[str, str],
    ) -> str:
        return "http://127.0.0.1:9000/signed-url"

    def _abort_multipart_upload(
        self,
        bucket_name: str,
        object_name: str,
        upload_id: str,
    ) -> None:
        self.aborted_upload = {
            "bucket_name": bucket_name,
            "object_name": object_name,
            "upload_id": upload_id,
        }

    def _complete_multipart_upload(
        self,
        bucket_name: str,
        object_name: str,
        upload_id: str,
        parts: list[dict],
    ) -> None:
        self.completed_upload = {
            "bucket_name": bucket_name,
            "object_name": object_name,
            "upload_id": upload_id,
            "parts": parts,
        }


class FailingMinioClient(FakeMinioClient):
    def bucket_exists(self, bucket_name: str) -> bool:
        raise S3Error(
            code="InvalidAccessKeyId",
            message="Invalid access key",
            resource=bucket_name,
            request_id="request-id",
            host_id="host-id",
            response=None,
        )


def test_adapter_creates_bucket_when_missing() -> None:
    client = FakeMinioClient(bucket_exists=False)

    MinioBlobStorageAdapter(
        client=client,
        bucket_name="bucket",
        signed_url_expires_seconds=3600,
    )

    assert client.created_bucket == "bucket"


def test_initialize_multipart_upload_returns_upload_id() -> None:
    adapter = MinioBlobStorageAdapter(
        client=FakeMinioClient(),
        bucket_name="bucket",
        signed_url_expires_seconds=3600,
    )

    upload_id = adapter.initialize_multipart_upload(
        object_key="datasets/id/raw/file.csv",
        content_type="text/csv",
    )

    assert upload_id == "upload-id"


def test_generate_signed_part_url_returns_url() -> None:
    adapter = MinioBlobStorageAdapter(
        client=FakeMinioClient(),
        bucket_name="bucket",
        signed_url_expires_seconds=3600,
    )

    upload_url = adapter.generate_signed_part_url(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
        part_number=1,
    )

    assert upload_url == "http://127.0.0.1:9000/signed-url"


def test_complete_multipart_upload_delegates_to_client() -> None:
    client = FakeMinioClient()
    adapter = MinioBlobStorageAdapter(
        client=client,
        bucket_name="bucket",
        signed_url_expires_seconds=3600,
    )
    parts = [{"part_number": 1, "etag": "etag-1"}]

    adapter.complete_multipart_upload(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
        parts=parts,
    )

    assert client.completed_upload == {
        "bucket_name": "bucket",
        "object_name": "datasets/id/raw/file.csv",
        "upload_id": "upload-id",
        "parts": parts,
    }


def test_abort_multipart_upload_delegates_to_client() -> None:
    client = FakeMinioClient()
    adapter = MinioBlobStorageAdapter(
        client=client,
        bucket_name="bucket",
        signed_url_expires_seconds=3600,
    )

    adapter.abort_multipart_upload(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
    )

    assert client.aborted_upload == {
        "bucket_name": "bucket",
        "object_name": "datasets/id/raw/file.csv",
        "upload_id": "upload-id",
    }


def test_cleanup_temporary_parts_returns_none() -> None:
    adapter = MinioBlobStorageAdapter(
        client=FakeMinioClient(),
        bucket_name="bucket",
        signed_url_expires_seconds=3600,
    )

    result = adapter.cleanup_temporary_parts(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
    )

    assert result is None


def test_ensure_bucket_exists_raises_s3_error() -> None:
    with pytest.raises(S3Error):
        MinioBlobStorageAdapter(
            client=FailingMinioClient(),
            bucket_name="bucket",
            signed_url_expires_seconds=3600,
        )