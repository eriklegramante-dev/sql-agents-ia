from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.preview.dependencies import get_dataset_preview_controller
from app.routes.preview.controllers.controller import (
    DatasetPreviewController,
)
from app.routes.preview.dtos.dto import (
    DatasetPreviewRequestDTO,
    DatasetPreviewResponseDTO,
)

router = APIRouter(
    prefix="/datasets",
)


@router.get(
    "/{dataset_id}/preview",
    response_model=DatasetPreviewResponseDTO,
)
async def get_dataset_preview(
    dataset_id: UUID,
    limit: int | None = Query(
    default=None,
    ge=1,
    le=100,
    description="Maximum number of rows returned in the preview.",

    ),
    controller: DatasetPreviewController = Depends(
        get_dataset_preview_controller
    ),

) -> DatasetPreviewResponseDTO:
    request = DatasetPreviewRequestDTO(
        dataset_id=dataset_id,
        limit=limit,
    )

    return await controller.execute(request)
