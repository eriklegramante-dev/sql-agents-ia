from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path

from app.prepare.dependencies import get_dataset_preparation_controller
from app.security.security import get_trusted_user_id
from app.prepare.exceptions import AppException
from app.routes.prepare.controllers.controller import DatasetPreparationController
from app.routes.prepare.dtos.dto import DatasetPreparationResponseDTO

router = APIRouter()


@router.post(
    "/datasets/{dataset_id}/prepare",
    response_model=DatasetPreparationResponseDTO,
    summary="Prepare dataset",
)
async def prepare_dataset(
    dataset_id: UUID = Path(..., description="Dataset UUID"),
    controller: DatasetPreparationController = Depends(
        get_dataset_preparation_controller
    ),
    user_id: int = Depends(get_trusted_user_id),
) -> DatasetPreparationResponseDTO:
    """
    Prepares a completed uploaded dataset for analytical processing.

    This endpoint validates the dataset identifier and delegates the request
    to the controller layer, which coordinates the service and workflow
    responsible for reading the raw dataset, inferring the schema,
    generating the prepared Parquet file, persisting metadata, and updating
    the dataset processing status.

    Authentication:
        Requires a valid internal signature and the trusted dataset owner identity.

    Args:
        user_id: Trusted caller identity used to authorize dataset ownership.
        dataset_id (UUID):
            Unique identifier of the dataset to prepare.
        controller (DatasetPreparationController):
            Controller responsible for orchestrating the dataset preparation
            use case.

    Returns:
        DatasetPreparationResponseDTO:
            Standardized success response containing the preparation result.

    Raises:
        HTTPException: Converts predictable application errors and unexpected
            failures into the API error envelope.
    """
    try:
        return await controller.prepare_dataset(dataset_id, user_id=user_id)

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
