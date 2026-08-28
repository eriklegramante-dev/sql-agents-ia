import asyncpg

from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.blob_storage_adapter import BlobStorageAdapter
from app.adapters.storage.local_storage_adapter import LocalStorageAdapter
from app.adapters.storage.minio_blob_storage_adapter import (
    MinioBlobStorageAdapter,
)
from app.adapters.storage.minio_multipart_client_adapter import (
    MinioMultipartClientAdapter,
)
from app.connections.minio import get_minio_client
from app.core.prepare.workflow import DatasetPreparationWorkflow
from app.database.dataset_repository import DatasetRepository
from app.routes.prepare.controllers.controller import (
    DatasetPreparationController,
)
from app.routes.prepare.services.service import DatasetPreparationService
from app.settings.setting import get_settings

_db_pool = None

async def get_db_pool() -> asyncpg.Pool:
    """
    Provides the shared asynchronous PostgreSQL connection pool.

    Creates the pool lazily using the configured database settings and reuses
    the same instance for subsequent dependency resolutions.

    Returns:
        asyncpg.Pool:
            Shared PostgreSQL connection pool.
    """
    global _db_pool

    if _db_pool is None:
        settings = get_settings()
        _db_pool = await asyncpg.create_pool(
            host=settings.database.host,
            port=settings.database.port,
            database=settings.database.name,
            user=settings.database.user,
            password=settings.database.password,
            min_size=settings.database.min_pool_size,
            max_size=settings.database.max_pool_size,
        )

    return _db_pool


async def get_dataset_repository() -> DatasetRepository:
    """
    Builds the dataset repository dependency.

    Resolves the shared database connection pool and injects it into the
    repository responsible for dataset metadata persistence.

    Returns:
        DatasetRepository:
            Repository instance configured with the shared database pool.
    """
    pool = await get_db_pool()
    return DatasetRepository(pool)


async def get_storage_adapter() -> StorageAdapter:
    """
    Build the storage adapter dependency.

    Selects the configured storage backend and returns an adapter that
    implements the StorageAdapter contract.

    Returns:
        StorageAdapter:
            MinIO storage adapter when configured, Azure Blob Storage adapter
            when configured, otherwise the local filesystem storage adapter.
    """
    settings = get_settings()

    if settings.storage.storage_type == "minio":
        minio_client = get_minio_client(settings=settings)

        multipart_client = MinioMultipartClientAdapter(
            client=minio_client,
        )

        return MinioBlobStorageAdapter(
            client=minio_client,
            multipart_client=multipart_client,
            bucket_name=settings.minio.bucket_name,
            signed_url_expires_seconds=(settings.upload.signed_url_expires_seconds),
        )

    if settings.storage.storage_type == "azure":
        return BlobStorageAdapter(settings.storage.azure_storage_connection_string)

    return LocalStorageAdapter(settings.storage.local_storage_path)


async def get_dataset_preparation_controller() -> DatasetPreparationController:
    """
    Builds the dataset preparation controller dependency.

    Wires the preparation controller with its service, workflow, repository,
    and storage adapter dependencies following the project architecture.

    Returns:
        DatasetPreparationController:
            Controller instance ready to handle dataset preparation requests.
    """
    repository = await get_dataset_repository()
    storage = await get_storage_adapter()

    workflow = DatasetPreparationWorkflow(repository, storage)
    service = DatasetPreparationService(workflow)

    return DatasetPreparationController(service)
