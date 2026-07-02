from uuid import UUID

from app.database.dataset_repository import DatasetRepository
from app.routes.schema.dtos.dto import (
    DatasetSchemaColumnDTO,
    DatasetSchemaResponseDataDTO,
)
from app.prepare.exceptions import ConflictException, NotFoundException
from app.enums.dataset_status import DatasetStatus

class DatasetSchemaWorkflow:
    """Orchestrates the dataset schema retrieval process.

    This workflow is responsible for validating the requested dataset,
    verifying that schema metadata exists, loading the persisted schema,
    and assembling the standardized response returned by the service
    layer.

    Business rules related to dataset schema retrieval are centralized
    in this workflow, while persistence operations remain delegated to
    the repository layer.
    """

    def __init__(
        self,
        dataset_repository: DatasetRepository,
    ) -> None:
        """Initializes the dataset schema workflow.

        Args:
            dataset_repository (DatasetRepository):
                Repository responsible for dataset lookup and schema
                persistence operations.
        """

        self.repository = dataset_repository

    async def execute(
        self,
        dataset_id: UUID,
    ) -> DatasetSchemaResponseDataDTO:
        """Retrieves the persisted schema for a prepared dataset.

        Validates that the requested dataset exists, verifies that schema
        metadata is available, retrieves the stored schema, and builds
        the response payload consumed by the service and controller
        layers.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset.

        Returns:
            DatasetSchemaResponseDataDTO:
                Response containing dataset metadata and the inferred
                schema associated with the dataset.

        Raises:
            NotFoundException:
                Raised when the dataset does not exist or when no schema
                metadata is available for the specified dataset.
        """

        dataset = await self.repository.get_by_id(dataset_id)

        if dataset is None:
            raise NotFoundException(
                f"Dataset with ID {dataset_id} not found."
            )

        schema = await self.repository.get_schema(dataset_id)

        if not schema:
            raise NotFoundException(
                f"No schema metadata found for dataset {dataset_id}."
            )

        if dataset.status.value != DatasetStatus.PREPARED:
            raise ConflictException(
                f"Dataset schema is not available yet. Please prepare the dataset first."
            )

        return DatasetSchemaResponseDataDTO(
            dataset_id=dataset.id,
            status=dataset.status.value,
            columns_count=len(schema),
            schema_columns=[
                DatasetSchemaColumnDTO(
                    name=column.name,
                    original_name=column.original_name,
                    type=column.data_type,
                    nullable=column.nullable,
                    sample_values=column.sample_values,
                    warnings=column.warnings,
                )
                for column in schema
            ],
            updated_at=dataset.updated_at,
        )