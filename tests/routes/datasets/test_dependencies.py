from unittest.mock import AsyncMock, Mock

import pytest

from app.adapters.storage.minio_blob_storage_adapter import (
    MinioBlobStorageAdapter,
)
from app.core.datasets.deletion_workflow import DatasetDeletionWorkflow
from app.core.datasets.list_workflow import DatasetListWorkflow
from app.core.datasets.workflow import DatasetWorkflow
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.dependencies import dependence
from app.routes.datasets.services.service import DatasetService


@pytest.mark.asyncio
async def test_get_dataset_repository_builds_postgres_repository(
    monkeypatch,
):
    """Build the dataset repository with the shared database pool."""
    fake_pool = Mock()

    get_db_pool = AsyncMock(
        return_value=fake_pool,
    )

    repository_class = Mock()
    repository_instance = Mock()
    repository_class.return_value = repository_instance

    monkeypatch.setattr(
        dependence,
        "get_db_pool",
        get_db_pool,
    )

    monkeypatch.setattr(
        dependence,
        "PostgresDatasetRepository",
        repository_class,
    )

    result = await dependence.get_dataset_repository()

    get_db_pool.assert_awaited_once_with()
    repository_class.assert_called_once_with(fake_pool)

    assert result is repository_instance


def test_get_dataset_storage_builds_minio_adapter(
    monkeypatch,
):
    """Build the dataset storage adapter from MinIO configuration."""
    fake_settings = Mock()

    fake_settings.minio.bucket_name = "sql-agents-raw"
    fake_settings.upload.signed_url_expires_seconds = 3600

    fake_minio_client = Mock()
    fake_multipart_client = Mock()
    fake_storage = Mock(spec=MinioBlobStorageAdapter)

    minio_client_factory = Mock(
        return_value=fake_minio_client,
    )

    multipart_client_class = Mock(
        return_value=fake_multipart_client,
    )

    storage_class = Mock(
        return_value=fake_storage,
    )

    monkeypatch.setattr(
        dependence,
        "get_settings",
        Mock(return_value=fake_settings),
    )

    monkeypatch.setattr(
        dependence,
        "get_minio_client",
        minio_client_factory,
    )

    monkeypatch.setattr(
        dependence,
        "MinioMultipartClientAdapter",
        multipart_client_class,
    )

    monkeypatch.setattr(
        dependence,
        "MinioBlobStorageAdapter",
        storage_class,
    )

    result = dependence.get_dataset_storage()

    minio_client_factory.assert_called_once_with(
        fake_settings,
    )

    multipart_client_class.assert_called_once_with(
        client=fake_minio_client,
    )

    storage_class.assert_called_once_with(
        client=fake_minio_client,
        multipart_client=fake_multipart_client,
        bucket_name="sql-agents-raw",
        signed_url_expires_seconds=3600,
    )

    assert result is fake_storage


@pytest.mark.asyncio
async def test_get_dataset_controller_builds_retrieval_and_deletion_workflows(
    monkeypatch,
):
    """Compose repository and storage into the dataset application layers."""
    fake_repository = Mock()
    fake_storage = Mock()
    fake_settings = Mock()

    fake_settings.minio.bucket_name = "sql-agents-raw"

    repository_factory = AsyncMock(
        return_value=fake_repository,
    )

    storage_factory = Mock(
        return_value=fake_storage,
    )

    monkeypatch.setattr(
        dependence,
        "get_dataset_repository",
        repository_factory,
    )

    monkeypatch.setattr(
        dependence,
        "get_dataset_storage",
        storage_factory,
    )

    monkeypatch.setattr(
        dependence,
        "get_settings",
        Mock(return_value=fake_settings),
    )

    controller = await dependence.get_dataset_controller()

    assert isinstance(
        controller,
        DatasetController,
    )

    assert isinstance(
        controller.service,
        DatasetService,
    )

    assert isinstance(
        controller.service.workflow,
        DatasetWorkflow,
    )

    assert isinstance(
        controller.service.deletion_workflow,
        DatasetDeletionWorkflow,
    )

    assert isinstance(controller.service.list_workflow, DatasetListWorkflow)
    assert controller.service.list_workflow.repository is fake_repository

    assert controller.service.workflow.repository is fake_repository

    assert controller.service.deletion_workflow.repository is fake_repository

    assert controller.service.deletion_workflow.storage is fake_storage

    assert controller.service.deletion_workflow.raw_container == "sql-agents-raw"
