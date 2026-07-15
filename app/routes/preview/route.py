from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.prepare.exceptions import AppException
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
    dataset_id: UUID = Path(
        ...,
        description="Unique identifier of the dataset.",
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=100,
        description="Maximum number of rows returned in the preview.",
    ),
    controller: DatasetPreviewController = Depends(
        get_dataset_preview_controller,
    ),
) -> DatasetPreviewResponseDTO:
    """Retrieves a limited preview of a prepared dataset."""

    try:
        request = DatasetPreviewRequestDTO(
            dataset_id=dataset_id,
            limit=limit,
        )

        return await controller.execute(request)

    except HTTPException:
        raise

    except AppException as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "success": False,
                "message": error.message,
                "data": None,
                "errors": error.details,
            },
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": (
                    "Internal server error during dataset preview retrieval."
                ),
                "data": None,
                "errors": [str(error)],
            },
        ) from error
