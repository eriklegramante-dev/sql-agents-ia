import asyncpg

from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.blob_storage_adapter import BlobStorageAdapter
from app.adapters.storage.local_storage_adapter import LocalStorageAdapter
from app.config.settings import settings
from app.database.dataset_repository import DatasetRepository
from app.routes.prepare.controllers.controller import DatasetPreparationController
from app.routes.prepare.services.service import DatasetPreparationService
from app.core.prepare.workflow import DatasetPreparationWorkflow

_db_pool: asyncpg.Pool | None = None


async def get_db_pool() -> asyncpg.Pool:
    global _db_pool

    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=settings.DB_MIN_POOL_SIZE,
            max_size=settings.DB_MAX_POOL_SIZE,
        )

    return _db_pool


async def get_dataset_repository() -> DatasetRepository:
    pool = await get_db_pool()
    return DatasetRepository(pool)


async def get_storage_adapter() -> StorageAdapter:
    if settings.STORAGE_TYPE == "azure":
        return BlobStorageAdapter(settings.AZURE_STORAGE_CONNECTION_STRING)

    return LocalStorageAdapter(settings.LOCAL_STORAGE_PATH)


async def get_dataset_preparation_controller() -> DatasetPreparationController:
    repository = await get_dataset_repository()
    storage = await get_storage_adapter()

    workflow = DatasetPreparationWorkflow(repository, storage)
    service = DatasetPreparationService(workflow)

    return DatasetPreparationController(service)
