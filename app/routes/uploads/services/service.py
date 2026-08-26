from typing import Any

from app.core.uploads.abort_workflow import UploadAbortWorkflow
from app.core.uploads.complete_workflow import UploadCompletionWorkflow
from app.core.uploads.workflow import UploadInitializationWorkflow
from app.logs.setup_logger import LOGGER
from app.routes.uploads.dtos.dto import UploadInitRequestDTO

from uuid import UUID


class UploadService:
    """Service layer responsible for orchestrating upload workflows.

    This service acts as an application layer between the HTTP controller
    and the upload workflows. It delegates each upload operation to its
    corresponding workflow while keeping controllers free from business
    orchestration logic.
    """

    def __init__(
        self,
        init_workflow: UploadInitializationWorkflow,
        complete_workflow: UploadCompletionWorkflow,
        abort_workflow: UploadAbortWorkflow,
    ) -> None:
        """Create a new upload service.

        Args:
            init_workflow:
                Workflow responsible for initializing multipart uploads.
            complete_workflow:
                Workflow responsible for completing multipart uploads.
            abort_workflow:
                Workflow responsible for aborting multipart uploads.
        """
        self.logger = LOGGER
        self.init_workflow = init_workflow
        self.complete_workflow = complete_workflow
        self.abort_workflow = abort_workflow

    async def initialize_upload(
        self,
        request: UploadInitRequestDTO,
    ) -> dict[str, Any]:
        """Initialize a multipart upload.

        Args:
            request:
                Validated upload initialization request.

        Returns:
            Dictionary containing the initialized upload metadata.
        """
        self.logger.log_info("[upload:init:service] Starting upload initialization")

        result = await self.init_workflow.run(request)

        self.logger.log_info("[upload:init:service] Upload initialization finished")

        return result

    async def complete_upload(
        self,
        dataset_id: UUID,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Complete a multipart upload.

        Args:
            dataset_id:
                Dataset identifier associated with the upload.
            upload_id:
                Multipart upload identifier.
            parts:
                Uploaded multipart parts.

        Returns:
            Dictionary containing the completed upload metadata.
        """
        self.logger.log_info("[upload:complete:service] Starting upload completion")

        result = await self.complete_workflow.run(
            dataset_id=dataset_id,
            upload_id=upload_id,
            parts=parts,
        )

        self.logger.log_info("[upload:complete:service] Upload completion finished")

        return result

    async def abort_upload(
        self,
        dataset_id: UUID,
        upload_id: str,
    ) -> dict[str, Any]:
        """Abort a multipart upload.

        Args:
            dataset_id:
                Dataset identifier associated with the upload.
            upload_id:
                Multipart upload identifier.

        Returns:
            Dictionary containing the final upload status.
        """
        self.logger.log_info("[upload:abort:service] Starting upload abort")

        result = await self.abort_workflow.run(
            dataset_id=dataset_id,
            upload_id=upload_id,
        )

        self.logger.log_info("[upload:abort:service] Upload abort finished")

        return result
