from uuid import UUID

from app.routes.prepare.dtos.dto import DatasetPreparationResponseData
from app.core.prepare.workflow import DatasetPreparationWorkflow


class DatasetPreparationService:
    """Application boundary for dataset preparation.

    Keeps the controller independent from workflow implementation details while
    delegating the preparation command to the workflow.

    Args:
        workflow (DatasetPreparationWorkflow): Core workflow that performs the
            dataset preparation steps.

    Attributes:
        workflow (DatasetPreparationWorkflow): Core preparation workflow
            dependency.
    """

    def __init__(self, workflow: DatasetPreparationWorkflow):
        self.workflow = workflow

    async def prepare_dataset(self, dataset_id: UUID) -> DatasetPreparationResponseData:
        """Run preparation for one dataset.

        Args:
            dataset_id (UUID): Identifier of the dataset to prepare.

        Returns:
            DatasetPreparationResponseData: Prepared dataset metadata returned
            by the workflow.
        """
        return await self.workflow.execute(dataset_id)
