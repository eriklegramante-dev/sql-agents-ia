from dataclasses import dataclass
from uuid import UUID

from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.exceptions import StorageOperationError
from app.core.datasets.models import DatasetMetadata
from app.core.datasets.repository import DatasetRepository
from app.enums.dataset_status import DatasetStatus
from app.logs.setup_logger import LoggerManager
from app.prepare.exceptions import NotFoundException


@dataclass(frozen=True)
class DatasetDeletionResult:
    """Result returned after processing a dataset deletion.

    Attributes:
        dataset: Dataset metadata after the deletion operation.
        already_deleted: Indicates whether the dataset was already marked
            as DELETED before the operation started.
    """

    dataset: DatasetMetadata
    already_deleted: bool = False


class DatasetDeletionWorkflow:
    """Workflow responsible for the dataset deletion lifecycle.

    Coordinates soft deletion of the dataset metadata, removal of related
    database records, and cleanup of the raw object from storage through
    injected abstractions.

    Attributes:
        repository: Repository used for dataset persistence operations.
        storage: Storage adapter used to remove the dataset raw object.
        raw_container: Logical container where raw dataset files are stored.
        logger: Logger used to record deletion workflow events.
    """

    def __init__(
        self,
        dataset_repository: DatasetRepository,
        storage: StorageAdapter,
        raw_container: str,
        logger: LoggerManager,
    ) -> None:
        """Initialize the dataset deletion workflow dependencies.

        Args:
            dataset_repository:
                Repository used to retrieve and update datasets.
            storage:
                Storage adapter used to remove dataset files.
            raw_container:
                Logical container containing raw dataset objects.
            logger:
                Logger injected by the application composition layer.
        """
        self.repository = dataset_repository
        self.storage = storage
        self.raw_container = raw_container
        self.logger = logger

    async def execute(
        self,
        dataset_id: UUID,
    ) -> DatasetDeletionResult:
        """Soft-delete a dataset and clean its related resources.

        Args:
            dataset_id:
                Unique identifier of the dataset to delete.

        Returns:
            Final dataset metadata and whether it had already been deleted.

        Raises:
            NotFoundException:
                If the dataset cannot be found or its final status cannot
                be persisted.
            StorageOperationError:
                If the raw dataset object cannot be removed from storage.
            DatasetRelatedRecordsDeletionException:
                If persistence cleanup for related records fails.
        """
        self.logger.log_info(
            f"[dataset:delete:workflow] Starting deletion for {dataset_id}"
        )

        dataset = await self.repository.get_metadata_by_id(
            dataset_id=dataset_id,
        )

        if dataset is None:
            raise NotFoundException(f"Dataset with ID {dataset_id} not found.")

        if dataset.status == DatasetStatus.DELETED.value:
            self.logger.log_info(
                f"[dataset:delete:workflow] Dataset {dataset_id} is already deleted"
            )

            return DatasetDeletionResult(
                dataset=dataset,
                already_deleted=True,
            )

        await self._delete_storage_object(
            dataset=dataset,
        )

        await self.repository.delete_related_records(
            dataset_id=dataset_id,
        )

        updated = await self.repository.update_status(
            dataset_id=dataset_id,
            status=DatasetStatus.DELETED,
        )

        if not updated:
            raise NotFoundException(
                f"Dataset with ID {dataset_id} could not be marked as deleted."
            )

        deleted_dataset = await self.repository.get_metadata_by_id(
            dataset_id=dataset_id,
        )

        if deleted_dataset is None:
            raise NotFoundException(
                f"Dataset with ID {dataset_id} not found after deletion."
            )

        self.logger.log_info(
            f"[dataset:delete:workflow] Dataset {dataset_id} deleted successfully"
        )

        return DatasetDeletionResult(
            dataset=deleted_dataset,
        )

    async def _delete_storage_object(
        self,
        dataset: DatasetMetadata,
    ) -> None:
        """Remove the dataset raw object and handle storage failures.

        Args:
            dataset:
                Dataset metadata containing the object key to remove.

        Raises:
            StorageOperationError:
                If the storage adapter fails while removing the object.
        """
        try:
            deleted = await self.storage.delete_file(
                container=self.raw_container,
                path=dataset.object_key,
            )

        except StorageOperationError as error:
            await self.repository.update_status(
                dataset_id=dataset.dataset_id,
                status=DatasetStatus.FAILED,
                error_message=str(error),
            )

            self.logger.log_error(
                f"[dataset:delete:workflow] Failed to remove storage "
                f"object for dataset {dataset.dataset_id}"
            )

            raise

        if not deleted:
            self.logger.log_info(
                f"[dataset:delete:workflow] Storage object for dataset "
                f"{dataset.dataset_id} was already absent"
            )
