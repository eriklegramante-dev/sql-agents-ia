from app.adapters.analysis.duckdb_query_adapter import DuckDBQueryAdapter
from app.analysis.sql_safety_validator import SQLSafetyValidator
from app.core.analysis.workflow import AnalysisQueryWorkflow
from app.logs.setup_logger import LOGGER
from app.prepare.dependencies import (
    get_dataset_repository,
    get_storage_adapter,
)
from app.routes.analysis.controllers.controller import AnalysisQueryController
from app.routes.analysis.services.service import AnalysisQueryService
from app.database.connection import get_db_pool
from app.database.query_execution_repository import QueryExecutionRepository

async def get_analysis_query_workflow() -> AnalysisQueryWorkflow:
    """
    Build the analysis query workflow dependency.

    Resolves the dataset repository and storage adapter, creates the SQL
    safety validator, DuckDB query adapter, and execution repository,
    and injects the dependencies into the analysis workflow.

    Returns:
        AnalysisQueryWorkflow:
            Fully configured workflow ready to execute analytical queries.
    """
    repository = await get_dataset_repository()
    storage_adapter = await get_storage_adapter()

    sql_validator = SQLSafetyValidator()
    query_adapter = DuckDBQueryAdapter()

    pool = await get_db_pool()
    execution_repository = QueryExecutionRepository(pool)

    return AnalysisQueryWorkflow(
        dataset_repository=repository,
        storage_adapter=storage_adapter,
        sql_validator=sql_validator,
        query_adapter=query_adapter,
        logger=LOGGER,
        execution_repository=execution_repository,
    )


async def get_analysis_query_service() -> AnalysisQueryService:
    """
    Build the analysis query service dependency.

    Creates the analysis workflow and injects it into the application service
    responsible for coordinating analytical query execution.

    Returns:
        AnalysisQueryService:
            Service configured with the analysis query workflow and logger.
    """
    workflow = await get_analysis_query_workflow()

    return AnalysisQueryService(
        workflow=workflow,
        logger=LOGGER,
    )


async def get_analysis_query_controller() -> AnalysisQueryController:
    """
    Build the analysis query controller dependency.

    Creates the application service and injects it into the controller used
    by the FastAPI analysis route.

    Returns:
        AnalysisQueryController:
            Controller configured with the required service and logger
            dependencies.
    """
    service = await get_analysis_query_service()

    return AnalysisQueryController(
        service=service,
        logger=LOGGER,
    )
