from typing import Optional

from app.core.preview.workflow import DatasetPreviewWorkflow
from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.preview.dtos.dto import (
    DatasetPreviewRequestDTO,
    DatasetPreviewResponseDataDTO,
)


class DatasetPreviewService:
    """
    Coordinates dataset preview service execution.

    This service delegates dataset preview processing to the workflow and
    returns the generated response data without containing business rules.

    Attributes:
        workflow:
            Workflow used to coordinate dataset preview processing.
        logger:
            Logger manager used during service execution.
    """

    def __init__(
        self,
        workflow: DatasetPreviewWorkflow,
        logger: LoggerManager | None = None,
    ) -> None:
        self.workflow = workflow
        self.logger = logger or LOGGER

    async def execute(
        self,
        request: DatasetPreviewRequestDTO,
    ) -> DatasetPreviewResponseDataDTO:
        self.logger.log_info(
            f"Executing dataset preview service for dataset " f"{request.dataset_id}."
        )

        response_data = await self.workflow.execute(request)

        self.logger.log_info(
            f"Dataset preview service completed for dataset " f"{request.dataset_id}."
        )

        return response_data
