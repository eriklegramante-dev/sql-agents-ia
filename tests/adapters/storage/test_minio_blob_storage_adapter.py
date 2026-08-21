from typing import Any

import pytest
from minio.error import S3Error

from app.adapters.storage.minio_blob_storage_adapter import (
    MinioBlobStorageAdapter,
)


class FakeMinioClient:
    def __init__(self, bucket_exists: bool = True) -> None:
        self.bucket_exists_result = bucket_exists
        self.created_bucket = None
        self.presigned_url_request = None

    def bucket_exists(self, bucket_name: str) -> bool:
        return self.bucket_exists_result

    def make_bucket(self, bucket_name: str) -> None:
        self.created_bucket = bucket_name

    def get_presigned_url(
        self,
        method: str,
        bucket_name: str,
        object_name: str,
        expires: Any,
        extra_query_params: dict[str, str],
    ) -> str:
        self.presigned_url_request = {
            "method": method,
            "bucket_name": bucket_name,
            "object_name": object_name,
            "expires": expires,
            "extra_query_params": extra_query_params,
        }
        return "http://127.0.0.1:9000/signed-url"


class FakeMultipartClient:
    def __init__(self) -> None:
        self.initialized_upload = None
        self.completed_upload = None
        self.aborted_upload = None

    def initialize(
        self,
        bucket_name: str,
        object_key: str,
        content_type: str,
    ) -> str:
        self.initialized_upload = {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "content_type": content_type,
        }
        return "upload-id"

    def complete(
        self,
        bucket_name: str,
        object_key: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> None:
        self.completed_upload = {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "upload_id": upload_id,
            "parts": parts,
        }

    def abort(
        self,
        bucket_name: str,
        object_key: str,
        upload_id: str,
    ) -> None:
        self.aborted_upload = {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "upload_id": upload_id,
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


def build_adapter(
    client: FakeMinioClient | None = None,
    multipart_client: FakeMultipartClient | None = None,
) -> tuple[
    MinioBlobStorageAdapter,
    FakeMinioClient,
    FakeMultipartClient,
]:
    selected_client = client or FakeMinioClient()
    selected_multipart_client = multipart_client or FakeMultipartClient()

    adapter = MinioBlobStorageAdapter(
        client=selected_client,
        multipart_client=selected_multipart_client,
        bucket_name="bucket",
        signed_url_expires_seconds=3600,
    )

    return adapter, selected_client, selected_multipart_client


def test_adapter_creates_bucket_when_missing() -> None:
    client = FakeMinioClient(bucket_exists=False)

    build_adapter(client=client)

    assert client.created_bucket == "bucket"


def test_initialize_multipart_upload_delegates_to_multipart_client() -> None:
    adapter, _, multipart_client = build_adapter()

    upload_id = adapter.initialize_multipart_upload(
        object_key="datasets/id/raw/file.csv",
        content_type="text/csv",
    )

    assert upload_id == "upload-id"
    assert multipart_client.initialized_upload == {
        "bucket_name": "bucket",
        "object_key": "datasets/id/raw/file.csv",
        "content_type": "text/csv",
    }


def test_generate_signed_part_url_returns_url() -> None:
    adapter, client, _ = build_adapter()

    upload_url = adapter.generate_signed_part_url(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
        part_number=1,
    )

    assert upload_url == "http://127.0.0.1:9000/signed-url"
    assert client.presigned_url_request is not None
    assert client.presigned_url_request["method"] == "PUT"
    assert client.presigned_url_request["bucket_name"] == "bucket"
    assert client.presigned_url_request["object_name"] == "datasets/id/raw/file.csv"
    assert client.presigned_url_request["extra_query_params"] == {
        "uploadId": "upload-id",
        "partNumber": "1",
    }


def test_complete_multipart_upload_delegates_to_multipart_client() -> None:
    adapter, _, multipart_client = build_adapter()
    parts = [
        {
            "part_number": 1,
            "etag": "etag-1",
        },
    ]

    adapter.complete_multipart_upload(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
        parts=parts,
    )

    assert multipart_client.completed_upload == {
        "bucket_name": "bucket",
        "object_key": "datasets/id/raw/file.csv",
        "upload_id": "upload-id",
        "parts": parts,
    }


def test_abort_multipart_upload_delegates_to_multipart_client() -> None:
    adapter, _, multipart_client = build_adapter()

    adapter.abort_multipart_upload(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
    )

    assert multipart_client.aborted_upload == {
        "bucket_name": "bucket",
        "object_key": "datasets/id/raw/file.csv",
        "upload_id": "upload-id",
    }


def test_cleanup_temporary_parts_returns_none() -> None:
    adapter, _, _ = build_adapter()

    result = adapter.cleanup_temporary_parts(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
    )

    assert result is None


def test_ensure_bucket_exists_raises_s3_error() -> None:
    with pytest.raises(S3Error):
        build_adapter(
            client=FailingMinioClient(),
        )
