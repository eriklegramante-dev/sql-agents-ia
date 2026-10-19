from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path

from app.security.security import get_trusted_user_id
from app.prepare.exceptions import AppException
from app.profiling.dependencies import get_dataset_profile_controller
from app.routes.profiling.controllers.controller import DatasetProfileController
from app.routes.profiling.dtos.dto import DatasetProfileResponseDTO

router = APIRouter(prefix="/datasets")


@router.post(
    "/{dataset_id}/profile",
    response_model=DatasetProfileResponseDTO,
    summary="Profile dataset",
)
async def profile_dataset(
    dataset_id: UUID = Path(..., description="Dataset UUID"),
    controller: DatasetProfileController = Depends(
        get_dataset_profile_controller,
    ),
    user_id: int = Depends(get_trusted_user_id),
) -> DatasetProfileResponseDTO:
    """
    Profile a prepared dataset.

    This endpoint receives a dataset identifier and delegates the profiling
    request to the controller layer. Predictable application errors are
    converted into the standardized HTTP error envelope used by the project.

    Args:
        user_id: Trusted caller identity used to authorize dataset ownership.
        dataset_id:
            Unique identifier of the dataset to profile.
        controller:
            Controller responsible for coordinating the profiling use case.

    Returns:
        DatasetProfileResponseDTO:
            Standardized response containing the generated dataset profile.

    Raises:
        HTTPException:
            Raised when a predictable application error or unexpected failure
            occurs during dataset profiling.
    """
    try:
        return await controller.profile_dataset(dataset_id, user_id=user_id)

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
                "message": "Internal server error during dataset profiling",
                "data": None,
                "errors": [str(error)],
            },
        )
