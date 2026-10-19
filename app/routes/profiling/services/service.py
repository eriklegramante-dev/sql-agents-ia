from typing import Optional
from uuid import UUID

from app.core.profiling.workflow import DatasetProfileWorkflow
from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.profiling.dtos.dto import DatasetProfileResponseDTO


class DatasetProfileService:
    """
    Service responsible for coordinating dataset profiling execution.

    This service acts as the application layer between the controller and the
    workflow. It delegates the profiling process to the workflow and returns
    its response without containing business rules, persistence logic, storage
    access, or FastAPI-specific behavior.

    Args:
        workflow:
            Workflow responsible for executing the dataset profiling process.
        logger:
            Logger manager used to record service execution events.

    Attributes:
        workflow:
            Workflow responsible for coordinating the profiling business logic.
        logger:
            Logger used to record service execution events.

    """

    def __init__(
        self,
        workflow: Optional[DatasetProfileWorkflow] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        self.workflow = workflow or DatasetProfileWorkflow()
        self.logger = (logger or LOGGER).logger

    async def profile_dataset(self, dataset_id: UUID, *, user_id: int) -> DatasetProfileResponseDTO:
        """
        Execute the dataset profiling workflow.

        Args:
            user_id: Trusted caller identity used to authorize dataset ownership.
            dataset_id:
                Unique identifier of the dataset to profile.

        Returns:
            DatasetProfileResponseDTO:
                Standardized response containing the generated profile.
        """
        self.logger.info("Executing dataset profiling service.")

        return await self.workflow.execute(dataset_id, user_id=user_id)
