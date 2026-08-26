from fastapi import APIRouter, Depends, HTTPException, status

from app.analysis.dependencies import get_analysis_query_controller
from app.routes.analysis.controllers.controller import AnalysisQueryController
from app.routes.analysis.dtos.dto import (
    AnalysisQueryRequestDTO,
    AnalysisQueryResponseDTO,
)

from app.routes.analysis.controllers.controller import AnalysisController
from app.routes.analysis.dependencies import get_analysis_controller
from app.routes.analysis.dtos.dto import (
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)
from app.security.security import verify_signature

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


@router.post(
    "/chart",
    response_model=AnalysisChartResponseDTO,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_signature)],
)
async def generate_chart(
    payload: AnalysisChartRequestDTO,
    controller: AnalysisController = Depends(get_analysis_controller),
) -> AnalysisChartResponseDTO:
    """
    Generates a simple chart specification for a prepared dataset.

    Executes read-only analytical SQL or plans a query based on a
    natural-language question, validating dataset status, chart type, and SQL
    safety before returning a frontend-ready chart specification.

    Args:
        payload:
            Request payload containing dataset identifier, chart configuration,
            or natural-language question.

        controller:
            Injected controller responsible for delegating chart generation.

    Returns:
        AnalysisChartResponseDTO:
            Standardized response containing executed SQL, chart specification,
            and data rows.

    Raises:
        HTTPException:
            Returns a 400 Bad Request status code if validation fails, the
            dataset is not prepared/profiled, or unsafe SQL is provided.
    """
    response = await controller.generate_chart(payload)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message,
        )
    return response
