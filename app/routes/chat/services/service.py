from app.chat.models import ChatMessageInput
from app.core.chat.workflow import ChatMessageWorkflow
from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.chat.dtos.dto import (
    ChatArtifactDTO,
    ChatMessageRequestDTO,
    ChatMessageResponseDataDTO,
)


class ChatMessageService:
    """
    Coordinates chat message processing at the application service layer.

    This service receives the validated HTTP request DTO, converts it into
    the internal input model expected by the chat workflow, delegates the
    business processing, and maps the workflow result into the response data
    DTO returned by the controller.

    The service contains no intent-detection, assistant-execution, dataset,
    query, or chart-generation rules. Those responsibilities remain isolated
    inside the workflow and its injected collaborators.

    Dependencies are received through constructor injection, preventing the
    service from creating concrete workflow or logging implementations.

    Args:
        workflow:
            Workflow responsible for orchestrating the complete chat message
            processing flow.

        logger:
            Optional logger manager used to record service execution events.

    Attributes:
        workflow:
            Workflow responsible for orchestrating the complete chat message
            processing flow.

        logger:
            Logger manager used to record service execution events.
    """

    def __init__(
        self,
        workflow: ChatMessageWorkflow,
        logger: LoggerManager | None = None,
    ) -> None:
        self._workflow = workflow
        self._logger = logger 

    async def execute(
        self,
        request: ChatMessageRequestDTO,
    ) -> ChatMessageResponseDataDTO:
        """
        Execute application-level chat message processing.

        Args:
            request:
                Validated chat request DTO received from the controller.

        Returns:
            Response data DTO containing the generated answer, detected intent,
            tool metadata, and optional artifact.
        """
        self._logger.log_info(
            f"Executing chat message service for user {request.user_id}."
        )

        workflow_input = ChatMessageInput(
            user_id=request.user_id,
            message=request.message,
            dataset_id=request.dataset_id,
            session_id=request.session_id,
            metadata=request.metadata,
        )

        result = await self._workflow.execute(workflow_input)

        artifact = None

        if result.artifact is not None:
            artifact = ChatArtifactDTO(
                type=result.artifact.type,
                content=result.artifact.content,
            )

        response_data = ChatMessageResponseDataDTO(
            user_id=result.user_id,
            session_id=result.session_id,
            answer=result.answer,
            intent=result.intent.value,
            tool_used=result.tool_used,
            dataset_id=result.dataset_id,
            artifact=artifact,
        )

        self._logger.log_info(
            f"Chat message service completed for user {request.user_id}."
        )

        return response_data
