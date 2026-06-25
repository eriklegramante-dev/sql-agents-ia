from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path

from app.prepare.dependencies import get_dataset_preparation_controller
from app.prepare.exceptions import AppException
from app.routes.prepare.controllers.controller import DatasetPreparationController

router = APIRouter()


@router.post("/datasets/{dataset_id}/prepare")
async def prepare_dataset(
    dataset_id: UUID = Path(..., description="Dataset UUID"),
    controller: DatasetPreparationController = Depends(
        get_dataset_preparation_controller
    ),
):
    try:
        return await controller.prepare_dataset(dataset_id)

    except AppException as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "success": False,
                "message": error.message,
                "data": None,
                "errors": error.details,
            },
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Internal server error during dataset preparation",
                "data": None,
                "errors": [str(error)],
            },
        )
