from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.minio_blob_storage_adapter import (
    MinioBlobStorageAdapter,
)
from app.adapters.storage.minio_multipart_client_adapter import (
    MinioMultipartClientAdapter,
)
from app.connections.minio import get_minio_client
from app.core.datasets.deletion_workflow import DatasetDeletionWorkflow
from app.core.datasets.repository import DatasetRepository
from app.core.datasets.workflow import DatasetWorkflow
from app.database.connection import get_db_pool
from app.database.dataset_repository import (
    DatasetRepository as PostgresDatasetRepository,
)
from app.logs.setup_logger import LOGGER
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.services.service import DatasetService
from app.settings.setting import get_settings


async def get_dataset_repository() -> DatasetRepository:
    """Create the dataset repository backed by the shared PostgreSQL pool.

    Returns:
        Repository implementation used by dataset retrieval and deletion
        workflows.
    """
    pool = await get_db_pool()

    return PostgresDatasetRepository(pool)


def get_dataset_storage() -> StorageAdapter:
    """Create the MinIO storage adapter used by dataset workflows.

    Returns:
        Storage adapter configured with the application MinIO client,
        bucket, multipart client, and signed URL expiration.
    """
    settings = get_settings()
    minio_client = get_minio_client(settings)

    multipart_client = MinioMultipartClientAdapter(
        client=minio_client,
    )

    return MinioBlobStorageAdapter(
        client=minio_client,
        multipart_client=multipart_client,
        bucket_name=settings.minio.bucket_name,
        signed_url_expires_seconds=settings.upload.signed_url_expires_seconds,
    )


async def get_dataset_controller() -> DatasetController:
    """Compose and return the dataset controller with all dependencies.

    Builds the repository and storage adapters, configures retrieval and
    deletion workflows, and injects them into the service and controller.

    Returns:
        Fully configured controller used by the dataset routes.
    """
    settings = get_settings()

    repository = await get_dataset_repository()
    storage = get_dataset_storage()

    retrieval_workflow = DatasetWorkflow(
        dataset_repository=repository,
        logger=LOGGER,
    )

    deletion_workflow = DatasetDeletionWorkflow(
        dataset_repository=repository,
        storage=storage,
        raw_container=settings.minio.bucket_name,
        logger=LOGGER,
    )

    service = DatasetService(
        workflow=retrieval_workflow,
        deletion_workflow=deletion_workflow,
        logger=LOGGER,
    )

    return DatasetController(
        service=service,
        logger=LOGGER,
    )
