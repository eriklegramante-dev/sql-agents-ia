from typing import Any

from app.core.uploads.dto import UploadInitRequestDTO
from app.core.uploads.init_workflow import UploadInitializationWorkflow
from app.logs.setup_logger import LOGGER


class UploadService:
    """Service responsible for exposing upload use cases.

    Attributes:
        init_workflow: Workflow responsible for upload initialization.
    """

    def __init__(self, init_workflow: UploadInitializationWorkflow) -> None:
        """Initialize the upload service.

        Args:
            init_workflow: Workflow responsible for upload initialization.
        """
        self.init_workflow = init_workflow

    def initialize_upload(
        self,
        request: UploadInitRequestDTO,
    ) -> dict[str, Any]:
        """Initialize a dataset upload.

        Args:
            request: Validated upload initialization request.

        Returns:
            Upload initialization result data.
        """
        LOGGER.log_info("[upload:init:service] Starting upload initialization")
        result = self.init_workflow.run(request)
        LOGGER.log_info("[upload:init:service] Upload initialization finished")
        return result
