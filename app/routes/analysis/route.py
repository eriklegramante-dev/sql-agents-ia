from fastapi import APIRouter, Depends, HTTPException, status

from app.analysis.dependencies import get_analysis_query_controller
from app.routes.analysis.controllers.controller import AnalysisQueryController
from app.routes.analysis.dtos.dto import (
    AnalysisQueryRequestDTO,
    AnalysisQueryResponseDTO,
)
from app.security.security import verify_signature, get_trusted_user_id
from app.routes.analysis.controllers.controller import AnalysisController
from app.routes.analysis.dependencies import get_analysis_controller
from app.routes.analysis.dtos.dto import (
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)

from app.routes.analysis.query_count import router as query_count_router
from app.security.security import verify_signature

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)

router.include_router(query_count_router)

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
    user_id: int = Depends(get_trusted_user_id),
) -> AnalysisQueryResponseDTO:
    """Delegate analysis using the identity supplied by the trusted caller.

    The workflow checks dataset ownership, validates and executes SQL,
    and records the completed query before a success response is returned.

    Args:
        payload: Validated dataset, SQL or question, and response limit.
        controller: Injected controller coordinating analysis processing.
        user_id: Positive identity forwarded with a valid internal signature.

    Returns:
        Standardized query result after the execution record is persisted.

    Raises:
        HTTPException: If security validation or controller execution fails.
    """
    return await controller.execute(payload, user_id=user_id)


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
