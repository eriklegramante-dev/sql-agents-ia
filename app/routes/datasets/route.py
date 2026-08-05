from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    status,
)

from app.prepare.exceptions import AppException
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.dependencies.dependence import (
    get_dataset_controller,
)
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
    dataset_id: UUID = Path(
        ...,
        description="Unique identifier of the dataset.",
    ),
    controller: DatasetController = Depends(
        get_dataset_controller,
    ),
):
    """Retrieve dataset metadata.

    Args:
        dataset_id: Unique identifier of the dataset.
        controller: Injected dataset controller.

    Returns:
        Standardized response containing dataset metadata.

    Raises:
        HTTPException:
            If validation or dataset retrieval fails.
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
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Internal server error.",
                "data": None,
                "errors": [str(error)],
            },
        )