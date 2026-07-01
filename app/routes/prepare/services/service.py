import logging
from typing import Optional
from uuid import UUID

from app.routes.prepare.dtos.dto import DatasetPreparationDataDTO
from app.core.prepare.workflow import DatasetPreparationWorkflow

logger = logging.getLogger(__name__)


class DatasetPreparationService:
    """
    Service responsible for coordinating dataset preparation execution.

    This service delegates the business rules to the preparation workflow and
    adds application-level logging around the operation.

    Attributes:
        workflow (DatasetPreparationWorkflow):
            Workflow responsible for executing the dataset preparation rules.
        logger (logging.Logger):
            Logger used to trace the service execution flow.
    """

    def __init__(
        self,
        workflow: DatasetPreparationWorkflow,
        service_logger: Optional[logging.Logger] = None,
    ):
        self.workflow = workflow
        self.logger = service_logger or logger

    async def prepare_dataset(self, dataset_id: UUID) -> DatasetPreparationDataDTO:
        """
        Runs dataset preparation for one dataset.

        Args:
            dataset_id (UUID):
                Identifier of the dataset to prepare.

        Returns:
            DatasetPreparationDataDTO:
                Prepared dataset metadata returned by the workflow.

        Raises:
            Exception:
                Re-raises any exception raised by the workflow after logging it.
        """
        self.logger.info(
            "Starting dataset preparation service for dataset %s", dataset_id
        )

        try:
            result = await self.workflow.execute(dataset_id)

            self.logger.info(
                "Dataset preparation service completed successfully for dataset %s",
                dataset_id,
            )

            return result

        except Exception:
            self.logger.exception(
                "Dataset preparation service failed for dataset %s",
                dataset_id,
            )
            raise
