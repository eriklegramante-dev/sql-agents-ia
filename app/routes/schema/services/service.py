from uuid import UUID
from typing import Optional

from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.schema.dtos.dto import DatasetSchemaResponseDataDTO
from app.core.schema.workflow import DatasetSchemaWorkflow


class DatasetSchemaService:
    """Coordinates the dataset schema retrieval operation.

    This service acts as the intermediary between the controller and the
    workflow layers. It receives requests from the controller, delegates
    the schema retrieval process to the workflow, and returns a standardized
    response object to the presentation layer.

    The service intentionally contains no business rules or persistence
    logic, ensuring that validation and retrieval responsibilities remain
    encapsulated within the workflow while keeping the controller free of
    implementation details.
    """

    def __init__(
        self,
        workflow: Optional[DatasetSchemaWorkflow] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        """Initializes the dataset schema service.

        Args:
            workflow (DatasetSchemaWorkflow):
                Workflow responsible for executing the dataset schema
                retrieval business logic.
        """

        self.logger = logger or LOGGER
        self.workflow = workflow or DatasetSchemaWorkflow(logger=self.logger)

    async def get_dataset_schema(
        self,
        dataset_id: UUID,
    ) -> DatasetSchemaResponseDataDTO:
        """Retrieves the persisted schema for the specified dataset.

        Delegates the request to the workflow responsible for validating
        the dataset, verifying schema availability, loading the persisted
        schema metadata, and constructing the standardized response object.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset whose schema should be
                retrieved.

        Returns:
            DatasetSchemaResponseDataDTO:
                Standardized response containing the dataset metadata and
                inferred schema information.
        """

        self.logger.log_info(
            f"Service layer: Initiating schema retrieval for dataset {dataset_id}."
        )

        response = await self.workflow.execute(dataset_id)

        self.logger.log_info(
            f"Dataset schema retrieval completed for dataset {dataset_id}."
        )
        return response
