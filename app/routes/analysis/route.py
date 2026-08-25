from fastapi import APIRouter, Depends, status

from app.analysis.dependencies import get_analysis_query_controller
from app.routes.analysis.controllers.controller import (
    AnalysisQueryController,
)
from app.routes.analysis.dtos.dto import (
    AnalysisQueryRequestDTO,
    AnalysisQueryResponseDTO,
)


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


@router.post(
    "/query",
    response_model=AnalysisQueryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Execute a dataset analysis query.",
    description=(
        "Executes a safe analytical query against a prepared or profiled "
        "dataset and returns the result in a tabular structure. Direct SQL "
        "queries are prioritized when both SQL and a natural-language "
        "question are provided."
    ),
)
async def execute_analysis_query(
    payload: AnalysisQueryRequestDTO,
    controller: AnalysisQueryController = Depends(
        get_analysis_query_controller,
    ),
) -> AnalysisQueryResponseDTO:
    """
    Execute a dataset analysis query.

    This route receives a validated analysis request, resolves the analysis
    controller through dependency injection, delegates the request processing
    to the application layers, and returns the standardized analytical query
    response.

    The route contains no dataset lookup, SQL validation, storage access, or
    query execution logic.

    Args:
        payload:
            Validated request containing the dataset identifier, optional
            natural-language question, optional direct SQL query, and row
            limit.

        controller:
            Analysis query controller resolved through FastAPI dependency
            injection.

    Returns:
        AnalysisQueryResponseDTO:
            Standardized response containing the executed SQL, returned
            columns, rows, row counts, and applied limit.
    """
    return await controller.execute(payload)