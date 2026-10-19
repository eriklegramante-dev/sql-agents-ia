from uuid import UUID

from app.routes.prepare.dtos.dto import DatasetPreparationResponseDTO
from app.routes.prepare.services.service import DatasetPreparationService


class DatasetPreparationController:
    """HTTP-facing adapter for dataset preparation.

    Calls the preparation service and wraps its DTO in the success response
    shape expected by the route.

    Args:
        service (DatasetPreparationService): Service that executes the dataset
            preparation use case.

    Attributes:
        service (DatasetPreparationService): Application service dependency.
    """

    def __init__(self, service: DatasetPreparationService):
        self.service = service

    async def prepare_dataset(self, dataset_id: UUID, *, user_id: int) -> dict:
        """Prepare a dataset and serialize the route response.

        Args:
            user_id: Trusted caller identity used to authorize dataset ownership.
            dataset_id (UUID): Identifier of the dataset to prepare.

        Returns:
            dict: API response envelope with success flag, message, serialized
            preparation data.
        """
        result = await self.service.prepare_dataset(dataset_id, user_id=user_id)

        response = DatasetPreparationResponseDTO(
            success=True,
            message="Dataset prepared successfully",
            data=result,
            errors=None,
        )

        return response.model_dump(mode="json", by_alias=True)
