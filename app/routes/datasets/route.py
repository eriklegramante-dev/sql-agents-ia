from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.prepare.exceptions import AppException
from app.security.security import get_trusted_user_id
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.dependencies.dependence import get_dataset_controller
from app.routes.datasets.dtos.dto import (
    DatasetDeleteResponseDTO,
    DatasetListResponseDTO,
    DatasetResponseDTO,
)

router = APIRouter(
    prefix="",
    tags=["Datasets"],
)

@router.get(
    "/datasets",
    response_model=DatasetListResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def list_datasets(
    user_id: Annotated[int, Depends(get_trusted_user_id)],
    controller: Annotated[
        DatasetController,
        Depends(get_dataset_controller),
    ],
) -> DatasetListResponseDTO:
    """List non-deleted dataset metadata owned by the trusted user.

    Args:
        user_id: Positive identity forwarded with a valid internal signature.
        controller: Injected controller responsible for dataset operations.

    Returns:
        Standardized response containing metadata owned by the trusted user.

    Raises:
        HTTPException:
            If the dataset listing fails due to an application error.
    """

    try:
        return await controller.list_datasets(
            user_id=user_id,
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
    user_id: int = Depends(get_trusted_user_id),
) -> DatasetResponseDTO:
    """Retrieve dataset metadata by its unique identifier.

    Args:
        user_id: Trusted caller identity used to authorize dataset ownership.
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
            user_id=user_id,
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
    user_id: int = Depends(get_trusted_user_id),
) -> DatasetDeleteResponseDTO:
    """Delete a dataset by its unique identifier.

    Args:
        user_id: Trusted caller identity used to authorize dataset ownership.
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
            user_id=user_id,
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
