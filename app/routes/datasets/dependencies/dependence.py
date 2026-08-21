from app.core.datasets.repository import DatasetRepository
from app.core.datasets.workflow import DatasetWorkflow
from app.database.connection import get_db_pool
from app.database.dataset_repository import (
    DatasetRepository as PostgresDatasetRepository,
)
from app.logs.setup_logger import LOGGER
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.services.service import DatasetService


async def get_dataset_repository() -> DatasetRepository:
    """
    Build the dataset repository using the shared PostgreSQL connection pool.
    """
    pool = await get_db_pool()

    return PostgresDatasetRepository(pool)


async def get_dataset_controller() -> DatasetController:
    """
    Build and return the configured dataset controller.
    """
    repository = await get_dataset_repository()

    workflow = DatasetWorkflow(
        dataset_repository=repository,
        logger=LOGGER,
    )

    service = DatasetService(
        workflow=workflow,
        logger=LOGGER,
    )

    return DatasetController(
        service=service,
        logger=LOGGER,
    )
