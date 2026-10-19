from uuid import UUID

from app.core.datasets.deletion_workflow import (
    DatasetDeletionResult,
    DatasetDeletionWorkflow,
)
from app.core.datasets.list_workflow import DatasetListWorkflow
from app.core.datasets.models import DatasetMetadata
from app.core.datasets.workflow import DatasetWorkflow
from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO


class DatasetService:
    """Service responsible for coordinating dataset operations.

    Converts core workflow results into response data used by the API layer
    while keeping persistence and HTTP concerns outside the service.

    Attributes:
        workflow: Workflow responsible for dataset retrieval.
        list_workflow: Workflow responsible for dataset listing.
        deletion_workflow: Workflow responsible for dataset deletion.
        logger: Logger used to record service execution events.
    """

    def __init__(
        self,
        workflow: DatasetWorkflow,
        list_workflow: DatasetListWorkflow,
        deletion_workflow: DatasetDeletionWorkflow,
        logger: LoggerManager | None = None,
    ) -> None:
        """Initialize the dataset service.

        Args:
            workflow: Workflow responsible for dataset retrieval.
            list_workflow: Workflow responsible for dataset listing.
            deletion_workflow: Workflow responsible for dataset deletion.
            logger: Optional logger used to register service events.
        """
        self.workflow = workflow
        self.list_workflow = list_workflow
        self.deletion_workflow = deletion_workflow
        self.logger = logger or LOGGER

    @staticmethod
    def _to_response_data(
        result: DatasetMetadata,
    ) -> DatasetResponseDataDTO:
        """Convert dataset domain metadata into API response data.

        Args:
            result: Dataset metadata returned by the core workflow.

        Returns:
            Dataset metadata formatted for the API response.
        """
        profile = result.profile

        return DatasetResponseDataDTO(
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
            total_nulls=(
                profile.total_nulls
                if profile is not None
                else None
            ),
            columns_with_nulls=(
                profile.columns_with_nulls
                if profile is not None
                else None
            ),
            numeric_columns=(
                profile.numeric_columns
                if profile is not None
                else None
            ),
            datetime_columns=(
                profile.datetime_columns
                if profile is not None
                else None
            ),
            text_columns=(
                profile.text_columns
                if profile is not None
                else None
            ),
            quality_warnings=(
                list(profile.quality_warnings)
                if profile is not None
                else None
            ),
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    async def list_datasets(
        self,
        *,
        user_id: int,
    ) -> list[DatasetResponseDataDTO]:
        """Map the trusted user's dataset listing to response data.

        Args:
            user_id: Trusted caller identity used to scope the repository lookup.

        Returns:
            Dataset metadata formatted for the API response.

        Repository failures propagate to the caller.
        """
        self.logger.log_info(
            "[dataset:list:service] Starting dataset listing"
        )

        datasets = await self.list_workflow.execute(user_id=user_id)

        response_data = [
            self._to_response_data(dataset)
            for dataset in datasets
        ]

        self.logger.log_info(
            f"[dataset:list:service] Dataset listing finished: "
            f"{len(response_data)} dataset(s)"
        )

        return response_data

    async def get_dataset(
        self,
        dataset_id: UUID,
        *,
        user_id: int,
    ) -> DatasetResponseDataDTO:
        """Retrieve dataset metadata and convert it to response data.

        Args:
            user_id: Trusted caller identity used to authorize dataset ownership.
            dataset_id: Unique identifier of the dataset to retrieve.

        Returns:
            Dataset metadata formatted for the API response.
        """
        self.logger.log_info(
            f"[dataset:get:service] Starting dataset retrieval for {dataset_id}"
        )

        result = await self.workflow.execute(
            dataset_id=dataset_id,
            user_id=user_id,
        )

        response_data = self._to_response_data(result)

        self.logger.log_info(
            "[dataset:get:service] Dataset retrieval finished"
        )

        return response_data

    async def delete_dataset(
        self,
        dataset_id: UUID,
        *,
        user_id: int,
    ) -> DatasetDeletionResult:
        """Execute the dataset deletion workflow.

        Args:
            user_id: Trusted caller identity used to authorize dataset ownership.
            dataset_id: Unique identifier of the dataset to delete.

        Returns:
            Result containing the final dataset deletion state.
        """
        self.logger.log_info(
            f"[dataset:delete:service] Starting dataset deletion for {dataset_id}"
        )

        result = await self.deletion_workflow.execute(
            dataset_id=dataset_id,
            user_id=user_id,
        )

        self.logger.log_info(
            f"[dataset:delete:service] Dataset deletion finished for {dataset_id}"
        )

        return result