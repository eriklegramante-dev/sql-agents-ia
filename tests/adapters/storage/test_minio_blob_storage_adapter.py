from typing import Any

import pytest
from minio.error import S3Error

from app.adapters.storage.exceptions import StorageOperationError
from app.adapters.storage.minio_blob_storage_adapter import (
    MinioBlobStorageAdapter,
)


class FakeObjectResponse:
    """Fake MinIO object response used by read-file tests."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.closed = False
        self.connection_released = False

    def read(self) -> bytes:
        """Return the configured object content."""
        return self.data

    def close(self) -> None:
        """Register that the object response was closed."""
        self.closed = True

    def release_conn(self) -> None:
        """Register that the underlying connection was released."""
        self.connection_released = True


class FakeMinioClient:
    """Fake MinIO client used by storage adapter tests."""

    def __init__(
        self,
        bucket_exists: bool = True,
        object_exists: bool = True,
        object_data: bytes = b"dataset-content",
    ) -> None:
        self.bucket_exists_result = bucket_exists
        self.object_exists = object_exists
        self.object_data = object_data

        self.created_bucket = None
        self.presigned_url_request = None
        self.stat_object_request = None
        self.get_object_request = None
        self.put_object_request = None
        self.removed_object = None
        self.last_object_response: FakeObjectResponse | None = None

    def bucket_exists(self, bucket_name: str) -> bool:
        """Return the configured bucket existence state."""
        return self.bucket_exists_result

    def make_bucket(self, bucket_name: str) -> None:
        """Register creation of a missing bucket."""
        self.created_bucket = bucket_name

    def get_presigned_url(
        self,
        method: str,
        bucket_name: str,
        object_name: str,
        expires: Any,
        extra_query_params: dict[str, str],
    ) -> str:
        """Register and return a fake signed upload URL."""
        self.presigned_url_request = {
            "method": method,
            "bucket_name": bucket_name,
            "object_name": object_name,
            "expires": expires,
            "extra_query_params": extra_query_params,
        }

        return "http://127.0.0.1:9000/signed-url"

    def get_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> FakeObjectResponse:
        """Return a fake stored object or simulate a missing object."""
        self.get_object_request = {
            "bucket_name": bucket_name,
            "object_name": object_name,
        }

        if not self.object_exists:
            raise S3Error(
                code="NoSuchKey",
                message="Object does not exist",
                resource=object_name,
                request_id="request-id",
                host_id="host-id",
                response=None,
            )

        response = FakeObjectResponse(
            data=self.object_data,
        )

        self.last_object_response = response

        return response

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: Any,
        length: int,
    ) -> None:
        """Register a MinIO object write operation."""
        self.put_object_request = {
            "bucket_name": bucket_name,
            "object_name": object_name,
            "data": data.read(),
            "length": length,
        }

    def stat_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> object:
        """Simulate checking whether a MinIO object exists."""
        self.stat_object_request = {
            "bucket_name": bucket_name,
            "object_name": object_name,
        }

        if not self.object_exists:
            raise S3Error(
                code="NoSuchKey",
                message="Object does not exist",
                resource=object_name,
                request_id="request-id",
                host_id="host-id",
                response=None,
            )

        return object()

    def remove_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        """Register removal of a MinIO object."""
        self.removed_object = {
            "bucket_name": bucket_name,
            "object_name": object_name,
        }


class FakeMultipartClient:
    """Fake multipart client used by MinIO adapter tests."""

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
        """Register multipart upload initialization."""
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
        """Register multipart upload completion."""
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
        """Register multipart upload cancellation."""
        self.aborted_upload = {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "upload_id": upload_id,
        }


class FailingMinioClient(FakeMinioClient):
    """Fake MinIO client that fails while checking the bucket."""

    def bucket_exists(self, bucket_name: str) -> bool:
        """Raise an S3 error while validating the bucket."""
        raise S3Error(
            code="InvalidAccessKeyId",
            message="Invalid access key",
            resource=bucket_name,
            request_id="request-id",
            host_id="host-id",
            response=None,
        )


class FailingObjectMinioClient(FakeMinioClient):
    """Fake MinIO client that fails while checking an object."""

    def stat_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> object:
        """Raise an unexpected S3 error for an object lookup."""
        raise S3Error(
            code="AccessDenied",
            message="Access denied",
            resource=object_name,
            request_id="request-id",
            host_id="host-id",
            response=None,
        )


class FailingReadMinioClient(FakeMinioClient):
    """Fake MinIO client that fails while reading an object."""

    def get_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> FakeObjectResponse:
        """Raise an unexpected S3 error during object retrieval."""
        raise S3Error(
            code="AccessDenied",
            message="Access denied",
            resource=object_name,
            request_id="request-id",
            host_id="host-id",
            response=None,
        )


class FailingWriteMinioClient(FakeMinioClient):
    """Fake MinIO client that fails while writing an object."""

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: Any,
        length: int,
    ) -> None:
        """Raise an unexpected S3 error during object storage."""
        raise S3Error(
            code="AccessDenied",
            message="Access denied",
            resource=object_name,
            request_id="request-id",
            host_id="host-id",
            response=None,
        )


class FailingRemoveMinioClient(FakeMinioClient):
    """Fake MinIO client that fails while removing an object."""

    def remove_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        """Raise an unexpected S3 error during object deletion."""
        raise S3Error(
            code="AccessDenied",
            message="Access denied",
            resource=object_name,
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
    """Build the MinIO storage adapter with fake dependencies."""
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
    """Create the configured MinIO bucket when it does not exist."""
    client = FakeMinioClient(bucket_exists=False)

    build_adapter(client=client)

    assert client.created_bucket == "bucket"


@pytest.mark.asyncio
async def test_read_file_returns_object_content() -> None:
    """Return stored object bytes and release the MinIO response."""
    client = FakeMinioClient(
        object_data=b"id,name\n1,Ana\n",
    )
    adapter, _, _ = build_adapter(
        client=client,
    )

    result = await adapter.read_file(
        container="bucket",
        path="datasets/id/raw/file.csv",
    )

    assert result == b"id,name\n1,Ana\n"

    assert client.get_object_request == {
        "bucket_name": "bucket",
        "object_name": "datasets/id/raw/file.csv",
    }

    assert client.last_object_response is not None
    assert client.last_object_response.closed is True
    assert client.last_object_response.connection_released is True


@pytest.mark.asyncio
async def test_read_file_raises_not_found_for_missing_object() -> None:
    """Raise FileNotFoundError when the requested object does not exist."""
    client = FakeMinioClient(
        object_exists=False,
    )
    adapter, _, _ = build_adapter(
        client=client,
    )

    with pytest.raises(FileNotFoundError):
        await adapter.read_file(
            container="bucket",
            path="datasets/id/raw/file.csv",
        )


@pytest.mark.asyncio
async def test_read_file_wraps_unexpected_s3_error() -> None:
    """Convert unexpected MinIO read failures into storage errors."""
    adapter, _, _ = build_adapter(
        client=FailingReadMinioClient(),
    )

    with pytest.raises(StorageOperationError):
        await adapter.read_file(
            container="bucket",
            path="datasets/id/raw/file.csv",
        )


@pytest.mark.asyncio
async def test_write_file_stores_object_content() -> None:
    """Write dataset bytes and return the stored object key."""
    adapter, client, _ = build_adapter()

    data = b"id,name\n1,Ana\n"

    result = await adapter.write_file(
        container="bucket",
        path="datasets/id/raw/file.csv",
        data=data,
    )

    assert result == "datasets/id/raw/file.csv"

    assert client.put_object_request == {
        "bucket_name": "bucket",
        "object_name": "datasets/id/raw/file.csv",
        "data": data,
        "length": len(data),
    }


@pytest.mark.asyncio
async def test_write_file_wraps_s3_error() -> None:
    """Convert MinIO write failures into storage operation errors."""
    adapter, _, _ = build_adapter(
        client=FailingWriteMinioClient(),
    )

    with pytest.raises(StorageOperationError):
        await adapter.write_file(
            container="bucket",
            path="datasets/id/raw/file.csv",
            data=b"dataset-content",
        )


def test_initialize_multipart_upload_delegates_to_multipart_client() -> None:
    """Delegate multipart initialization to the multipart client."""
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
    """Return the signed URL generated by the MinIO client."""
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
    """Delegate multipart completion to the multipart client."""
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
    """Delegate multipart cancellation to the multipart client."""
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
    """Return None for the current temporary parts cleanup implementation."""
    adapter, _, _ = build_adapter()

    result = adapter.cleanup_temporary_parts(
        object_key="datasets/id/raw/file.csv",
        upload_id="upload-id",
    )

    assert result is None


@pytest.mark.asyncio
async def test_file_exists_returns_true_for_existing_object() -> None:
    """Return True when the requested MinIO object exists."""
    adapter, client, _ = build_adapter()

    result = await adapter.file_exists(
        container="bucket",
        path="datasets/id/raw/file.csv",
    )

    assert result is True
    assert client.stat_object_request == {
        "bucket_name": "bucket",
        "object_name": "datasets/id/raw/file.csv",
    }


@pytest.mark.asyncio
async def test_file_exists_returns_false_for_missing_object() -> None:
    """Return False when the requested MinIO object does not exist."""
    client = FakeMinioClient(object_exists=False)
    adapter, _, _ = build_adapter(client=client)

    result = await adapter.file_exists(
        container="bucket",
        path="datasets/id/raw/file.csv",
    )

    assert result is False


@pytest.mark.asyncio
async def test_delete_file_removes_existing_object() -> None:
    """Remove the requested MinIO object when it exists."""
    adapter, client, _ = build_adapter()

    result = await adapter.delete_file(
        container="bucket",
        path="datasets/id/raw/file.csv",
    )

    assert result is True
    assert client.removed_object == {
        "bucket_name": "bucket",
        "object_name": "datasets/id/raw/file.csv",
    }


@pytest.mark.asyncio
async def test_delete_file_returns_false_when_object_is_missing() -> None:
    """Return False when the requested object was already absent."""
    client = FakeMinioClient(object_exists=False)
    adapter, _, _ = build_adapter(client=client)

    result = await adapter.delete_file(
        container="bucket",
        path="datasets/id/raw/file.csv",
    )

    assert result is False
    assert client.removed_object is None


@pytest.mark.asyncio
async def test_file_exists_wraps_unexpected_s3_error() -> None:
    """Convert unexpected object lookup failures into storage errors."""
    adapter, _, _ = build_adapter(
        client=FailingObjectMinioClient(),
    )

    with pytest.raises(StorageOperationError):
        await adapter.file_exists(
            container="bucket",
            path="datasets/id/raw/file.csv",
        )


@pytest.mark.asyncio
async def test_delete_file_propagates_storage_operation_error() -> None:
    """Propagate storage errors raised while checking the object."""
    adapter, _, _ = build_adapter(
        client=FailingObjectMinioClient(),
    )

    with pytest.raises(StorageOperationError):
        await adapter.delete_file(
            container="bucket",
            path="datasets/id/raw/file.csv",
        )


@pytest.mark.asyncio
async def test_delete_file_wraps_remove_object_s3_error() -> None:
    """Convert MinIO object-removal failures into storage errors."""
    adapter, _, _ = build_adapter(
        client=FailingRemoveMinioClient(),
    )

    with pytest.raises(StorageOperationError):
        await adapter.delete_file(
            container="bucket",
            path="datasets/id/raw/file.csv",
        )


def test_ensure_bucket_exists_raises_s3_error() -> None:
    """Propagate MinIO errors raised while validating the bucket."""
    with pytest.raises(S3Error):
        build_adapter(
            client=FailingMinioClient(),
        )
