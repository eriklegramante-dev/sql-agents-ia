from app.core.datasets.models import DatasetMetadata
from app.core.datasets.repository import DatasetRepository
from app.logs.setup_logger import LOGGER, LoggerManager


class DatasetListWorkflow:
    """Workflow responsible for listing dataset metadata.

    The workflow belongs to the core layer and depends only on the dataset
    repository abstraction and domain models.
    """

    def __init__(
        self,
        dataset_repository: DatasetRepository,
        logger: LoggerManager | None = None,
    ) -> None:
        """Initialize the dataset listing workflow.

        Args:
            dataset_repository:
                Repository responsible for retrieving dataset metadata.
            logger:
                Logger used to register workflow execution events.
        """
        self.repository = dataset_repository
        self.logger = logger or LOGGER

    async def execute(
        self,
        *,
        user_id: int,
    ) -> list[DatasetMetadata]:
        """Retrieve non-deleted metadata for the trusted user.

        Args:
            user_id: Trusted caller identity used to scope the repository lookup.

        Returns:
            Dataset metadata ordered from newest to oldest.

        Repository failures propagate to the caller.
        """

        self.logger.log_info(
            "[dataset:list:workflow] Starting dataset listing"
        )

        datasets = await self.repository.list_metadata(user_id=user_id)

        self.logger.log_info(
            f"[dataset:list:workflow] Dataset listing completed: "
            f"{len(datasets)} dataset(s)"
        )

        return datasets
