from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.prepare.exceptions import AppException
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.dependencies.dependence import get_dataset_controller
from app.routes.datasets.dtos.dto import (
    DatasetDeleteResponseDTO,
    DatasetResponseDTO,
)

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
    """Retrieve dataset metadata by its unique identifier.

    Args:
        dataset_id: Unique identifier of the dataset to retrieve.
        controller: Injected controller responsible for dataset operations.

    Returns:
        Standardized response containing the requested dataset metadata.

    Raises:
        HTTPException:
            If the dataset cannot be retrieved due to an application error.
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


@router.delete(
    "/datasets/{dataset_id}",
    response_model=DatasetDeleteResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def delete_dataset(
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
) -> DatasetDeleteResponseDTO:
    """Delete a dataset by its unique identifier.

    Args:
        dataset_id: Unique identifier of the dataset to delete.
        controller: Injected controller responsible for dataset operations.

    Returns:
        Standardized response containing the dataset final deletion state.

    Raises:
        HTTPException:
            If the dataset deletion fails due to an application error.
    """
    try:
        return await controller.delete_dataset(
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
