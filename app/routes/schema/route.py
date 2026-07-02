from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path

from app.prepare.exceptions import AppException
from app.routes.schema.controllers.controller import DatasetSchemaController
from app.routes.schema.dependencies.dependence import get_dataset_schema_controller


router = APIRouter()


@router.get("/datasets/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: UUID = Path(..., description="Dataset UUID"),
    controller: DatasetSchemaController = Depends(get_dataset_schema_controller),
):
    """Retrieves the persisted inferred schema for a prepared dataset.

    Receives a dataset identifier from the URL path, delegates schema
    retrieval to the dataset schema controller, and returns the standardized
    API response. Business rules and persistence access remain isolated in
    the workflow and repository layers.

    Args:
        dataset_id (UUID):
            Unique identifier of the dataset whose inferred schema should
            be retrieved.

    Returns:
        dict:
            Standardized response containing dataset metadata and persisted
            schema information.

    Raises:
        HTTPException:
            Raised when schema retrieval fails due to a known application
            error or an unexpected internal error.
    """

    try:
        return await controller.get_dataset_schema(dataset_id)

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
                "message": "Internal server error during dataset schema retrieval",
                "data": None,
                "errors": [str(error)],
            },
        )
