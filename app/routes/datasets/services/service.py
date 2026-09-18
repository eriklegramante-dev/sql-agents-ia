from uuid import UUID

from app.core.datasets.deletion_workflow import (
    DatasetDeletionResult,
    DatasetDeletionWorkflow,
)
from app.core.datasets.workflow import DatasetWorkflow
from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO


class DatasetService:
    """Service responsible for coordinating dataset operations.

    Converts core workflow results into response data used by the API layer
    while keeping persistence and HTTP concerns outside the service.

    Attributes:
        workflow: Workflow responsible for dataset retrieval.
        deletion_workflow: Workflow responsible for dataset deletion.
        logger: Logger used to record service execution events.
    """

    def __init__(
        self,
        workflow: DatasetWorkflow,
        deletion_workflow: DatasetDeletionWorkflow,
        logger: LoggerManager | None = None,
    ) -> None:
        """Initialize the dataset service.

        Args:
            workflow: Workflow responsible for dataset retrieval.
            deletion_workflow: Workflow responsible for dataset deletion.
            logger: Optional logger used to register service events.
        """
        self.workflow = workflow
        self.deletion_workflow = deletion_workflow
        self.logger = logger or LOGGER

    async def get_dataset(
        self,
        dataset_id: UUID,
    ) -> DatasetResponseDataDTO:
        """Retrieve dataset metadata and convert it to response data.

        Args:
            dataset_id: Unique identifier of the dataset to retrieve.

        Returns:
            Dataset metadata formatted for the API response.
        """
        self.logger.log_info(
            f"[dataset:get:service] Starting dataset retrieval for {dataset_id}"
        )

        result = await self.workflow.execute(
            dataset_id=dataset_id,
        )

        response_data = DatasetResponseDataDTO(
            dataset_id=result.dataset_id,
            name=result.name,
            original_filename=result.original_filename,
            content_type=result.content_type,
            file_size_bytes=result.file_size_bytes,
            status=result.status,
            object_key=result.object_key,
            description=result.description,
            rows_count=result.rows_count,
            columns_count=result.columns_count,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

        self.logger.log_info("[dataset:get:service] Dataset retrieval finished")

        return response_data

    async def delete_dataset(
        self,
        dataset_id: UUID,
    ) -> DatasetDeletionResult:
        """Execute the dataset deletion workflow.

        Args:
            dataset_id: Unique identifier of the dataset to delete.

        Returns:
            Result containing the final dataset deletion state.
        """
        self.logger.log_info(
            f"[dataset:delete:service] Starting dataset deletion for {dataset_id}"
        )

        result = await self.deletion_workflow.execute(
            dataset_id=dataset_id,
        )

        self.logger.log_info(
            f"[dataset:delete:service] Dataset deletion finished for {dataset_id}"
        )

        return result
