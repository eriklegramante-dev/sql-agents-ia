from fastapi import APIRouter, Depends, HTTPException, status

from app.routes.analysis.controllers.controller import AnalysisController
from app.routes.analysis.dependencies import get_analysis_controller
from app.routes.analysis.dtos.dto import (
    AnalysisChartRequestDTO,
    AnalysisChartResponseDTO,
)
from app.security.security import verify_signature

router = APIRouter(prefix="/analysis", tags=["Analysis"])


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
