from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.prepare.exceptions import AppException
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.dependencies.dependence import get_dataset_controller
from app.routes.datasets.dtos.dto import DatasetResponseDTO

router = APIRouter(
    prefix="",
    tags=["Datasets"],
)


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_dataset(
    dataset_id: Annotated[
        UUID,
        Path(
            description="Unique identifier of the dataset.",
        ),
    ],
    controller: Annotated[
        DatasetController,
        Depends(get_dataset_controller),
    ],
) -> DatasetResponseDTO:
    """Retrieve dataset metadata.

    Args:
        dataset_id: Unique identifier of the dataset.
        controller: Injected dataset controller.

    Returns:
        Standardized response containing dataset metadata.

    Raises:
        HTTPException:
            If dataset retrieval fails with an expected application error.
    """
    try:
        return await controller.get_dataset(
            dataset_id=dataset_id,
        )

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