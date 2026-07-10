from typing import Any

from app.core.uploads.abort_workflow import UploadAbortWorkflow
from app.core.uploads.complete_workflow import UploadCompletionWorkflow
from app.core.uploads.workflow import UploadInitializationWorkflow
from app.logs.setup_logger import LOGGER


class UploadService:
    """Service responsible for exposing upload use cases.

    Attributes:
        workflow: Workflow responsible for upload initialization.
        init_workflow: Alias for the upload initialization workflow.
        complete_workflow: Workflow responsible for upload completion.
        abort_workflow: Workflow responsible for upload abort.

    Args:
        init_workflow: Upload initialization workflow used by this service.
        complete_workflow: Upload completion workflow used by this service.
        abort_workflow: Upload abort workflow used by this service.
    """

    def __init__(
        self,
        init_workflow: UploadInitializationWorkflow,
        complete_workflow: UploadCompletionWorkflow,
        abort_workflow: UploadAbortWorkflow,
    ) -> None:
        """Initialize the upload service.

        Args:
            init_workflow: Workflow used to initialize uploads.
            complete_workflow: Workflow used to complete uploads.
            abort_workflow: Workflow used to abort uploads.
        """
        self.workflow = init_workflow
        self.init_workflow = init_workflow
        self.complete_workflow = complete_workflow
        self.abort_workflow = abort_workflow

    def initialize_upload(self, request: Any) -> dict[str, Any]:
        """Initialize a dataset upload.

        Args:
            request: Validated upload initialization request.

        Returns:
            Upload initialization result data.
        """
        LOGGER.log_info("[upload:init:service] Starting upload initialization")
        result = self.workflow.run(request)
        LOGGER.log_info("[upload:init:service] Upload initialization finished")
        return result

    def complete_upload(
        self,
        dataset_id: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Complete a dataset multipart upload.

        Args:
            dataset_id: Dataset identifier associated with the upload.
            upload_id: Multipart upload identifier to complete.
            parts: Uploaded multipart parts.

        Returns:
            Upload completion result data.
        """
        LOGGER.log_info("[upload:complete:service] Starting upload completion")
        result = self.complete_workflow.run(
            dataset_id=dataset_id,
            upload_id=upload_id,
            parts=parts,
        )
        LOGGER.log_info("[upload:complete:service] Upload completion finished")
        return result

    def abort_upload(
        self,
        dataset_id: str,
        upload_id: str,
    ) -> dict[str, Any]:
        """Abort an unfinished dataset upload.

        Args:
            dataset_id: Dataset identifier associated with the upload.
            upload_id: Multipart upload identifier to abort.

        Returns:
            Upload abort result data.
        """
        LOGGER.log_info("[upload:abort:service] Starting upload abort")
        result = self.abort_workflow.run(
            dataset_id=dataset_id,
            upload_id=upload_id,
        )
        LOGGER.log_info("[upload:abort:service] Upload abort finished")
        return result
