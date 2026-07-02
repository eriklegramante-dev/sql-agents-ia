import asyncpg

from app.database.dataset_repository import DatasetRepository
from app.routes.schema.controllers.controller import DatasetSchemaController
from app.routes.schema.services.service import DatasetSchemaService
from app.core.schema.workflow import DatasetSchemaWorkflow
from app.settings.setting import get_settings

_db_pool: asyncpg.Pool | None = None


async def get_db_pool() -> asyncpg.Pool:
    """Provides the shared asynchronous PostgreSQL connection pool.

    Creates the database connection pool lazily using the configured
    application settings and reuses the same instance across dependency
    resolutions.

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
    """Builds the dataset repository dependency.

    Resolves the shared database connection pool and injects it into the
    repository responsible for dataset metadata and schema persistence
    operations.

    Returns:
        DatasetRepository:
            Repository instance configured with the shared database pool.
    """
    pool = await get_db_pool()
    return DatasetRepository(pool)


async def get_dataset_schema_controller() -> DatasetSchemaController:
    """Builds the dataset schema controller dependency.

    Wires the schema controller with its service, workflow, and repository
    dependencies following the project's architectural pattern.

    Returns:
        DatasetSchemaController:
            Controller instance ready to handle dataset schema retrieval
            requests.
    """
    repository = await get_dataset_repository()

    workflow = DatasetSchemaWorkflow(repository)
    service = DatasetSchemaService(workflow)

    return DatasetSchemaController(service)