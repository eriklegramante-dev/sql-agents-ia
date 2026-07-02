from uuid import UUID

from app.routes.schema.dtos.dto import DatasetSchemaResponseDTO
from app.routes.schema.services.service import DatasetSchemaService


class DatasetSchemaController:
    """Coordinates requests for dataset schema retrieval.

    This controller acts as the entry point for the dataset schema feature
    within the application layer. It receives validated requests from the
    route, delegates the retrieval process to the service layer, and
    assembles the standardized response returned to the API.

    The controller intentionally contains no business rules or persistence
    logic. Its responsibility is limited to request orchestration and
    response construction, allowing the workflow to remain the single
    source of truth for business behavior.
    """

    def __init__(
        self,
        service: DatasetSchemaService,
    ) -> None:
        """Initializes the dataset schema controller.

        Args:
            service (DatasetSchemaService):
                Service responsible for coordinating the dataset schema
                retrieval process.
        """

        self.service = service

    async def get_dataset_schema(
        self,
        dataset_id: UUID,
    ) -> DatasetSchemaResponseDTO:
        """Retrieves the persisted schema for the specified dataset.

        Delegates the request to the service layer, which coordinates the
        workflow responsible for validating the dataset, loading the
        persisted schema metadata, and building the response payload.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset whose schema should be
                retrieved.

        Returns:
            DatasetSchemaResponseDTO:
                Standardized response indicating whether the operation
                succeeded and containing the requested schema metadata.
        """

        response_data = await self.service.get_dataset_schema(dataset_id)

        return DatasetSchemaResponseDTO(
            success=True,
            message="Dataset schema retrieved successfully.",
            data=response_data,
        ).model_dump(mode="json", by_alias=True)