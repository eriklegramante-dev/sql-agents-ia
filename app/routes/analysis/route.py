from fastapi import APIRouter, Depends, HTTPException, status
from app.routes.analysis.controllers.controller import AnalysisController
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
def generate_chart(
    payload: AnalysisChartRequestDTO,
    controller: AnalysisController = Depends(),
) -> AnalysisChartResponseDTO:
    response = controller.generate_chart(payload)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message,
        )
    return response