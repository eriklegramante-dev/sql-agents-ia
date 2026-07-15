from pathlib import Path

import asyncpg

from app.core.preview.workflow import DatasetPreviewWorkflow
from app.database.dataset_repository import DatasetRepository
from app.logs.setup_logger import LOGGER
from app.routes.preview.controllers.controller import DatasetPreviewController
from app.routes.preview.services.service import DatasetPreviewService
from app.settings.setting import get_settings
from app.adapters.storage.local_storage_adapter import LocalStorageAdapter

_db_pool: asyncpg.Pool | None = None


async def get_db_pool() -> asyncpg.Pool:
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
    pool = await get_db_pool()
    return DatasetRepository(pool)


def get_storage_adapter() -> LocalStorageAdapter:
    return LocalStorageAdapter(
        base_path=Path("storage"),
    )


async def get_dataset_preview_controller() -> DatasetPreviewController:
    repository = await get_dataset_repository()
    storage_adapter = get_storage_adapter()

    workflow = DatasetPreviewWorkflow(
        dataset_repository=repository,
        storage_adapter=storage_adapter,
        logger=LOGGER,
    )

    service = DatasetPreviewService(
        workflow=workflow,
        logger=LOGGER,
    )

    return DatasetPreviewController(
        service=service,
        logger=LOGGER,
    )