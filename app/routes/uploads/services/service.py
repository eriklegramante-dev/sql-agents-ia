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
        *,
        user_id: int,
    ) -> dict[str, Any]:
        """Initialize a multipart upload for the trusted user.

        Args:
            request:
                Validated upload initialization request.
            user_id:
                Trusted caller identity forwarded to the workflow.

        Returns:
            Dictionary containing identifiers, object key, upload status,
            chunk planning, and signed part URLs.

        Raises:
            ValueError: If the workflow rejects the identity or upload constraints.

        Other workflow failures propagate to the controller.
        """
        self.logger.log_info("[upload:init:service] Starting upload initialization")

        result = await self.init_workflow.run(request=request, user_id=user_id)

        self.logger.log_info("[upload:init:service] Upload initialization finished")

        return result

    async def complete_upload(
        self,
        dataset_id: UUID,
        upload_id: str,
        parts: list[dict[str, Any]],
        *,
        user_id: int,
    ) -> dict[str, Any]:
        """Delegate completion of an upload owned by the trusted user.

        Args:
            dataset_id:
                Dataset identifier associated with the upload.
            upload_id:
                Multipart upload identifier.
            parts:
                Uploaded part numbers and ETags to forward to the workflow.
            user_id:
                Trusted caller identity forwarded to the workflow.

        Returns:
            Dictionary containing the completed upload metadata.

        Raises:
            UploadAccessDeniedError: If the caller does not own the upload.
            ValueError: If upload metadata or parts are invalid.
            UploadCompletionError: If object storage cannot complete the upload.

        Other workflow failures propagate to the controller.
        """
        self.logger.log_info("[upload:complete:service] Starting upload completion")

        result = await self.complete_workflow.run(
            dataset_id=dataset_id,
            upload_id=upload_id,
            parts=parts,
            user_id=user_id,
        )

        self.logger.log_info("[upload:complete:service] Upload completion finished")

        return result

    async def abort_upload(
        self,
        dataset_id: UUID,
        upload_id: str,
        *,
        user_id: int,
    ) -> dict[str, Any]:
        """Delegate cancellation of an upload owned by the trusted user.

        Args:
            dataset_id:
                Dataset identifier associated with the upload.
            upload_id:
                Multipart upload identifier.
            user_id:
                Trusted caller identity forwarded to the workflow.

        Returns:
            Dictionary containing the final upload and dataset statuses.

        Raises:
            UploadAccessDeniedError: If the caller does not own the upload.
            ValueError: If the upload does not exist or cannot be aborted.
            RuntimeError: If storage abort or cleanup fails.

        Other workflow failures propagate to the controller.
        """
        self.logger.log_info("[upload:abort:service] Starting upload abort")

        result = await self.abort_workflow.run(
            dataset_id=dataset_id,
            upload_id=upload_id,
            user_id=user_id,
        )

        self.logger.log_info("[upload:abort:service] Upload abort finished")

        return result
