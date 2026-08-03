from uuid import UUID

from app.adapters.chat.assistant_adapter import AssistantAdapter
from app.adapters.chat.chart_tool_adapter import ChartToolAdapter
from app.adapters.chat.query_tool_adapter import QueryToolAdapter
from app.chat.intent_detector import ChatIntentDetector
from app.chat.models import ChartResult, ChatPreferences, QueryResult
from app.core.agent_preferences.workflow import AgentPreferencesWorkflow
from app.core.chat.workflow import ChatMessageWorkflow
from app.logs.setup_logger import LOGGER
from app.routes.chat.controllers.controller import ChatMessageController
from app.routes.chat.services.service import ChatMessageService


async def execute_default_assistant(
    message: str,
    preferences: ChatPreferences,
) -> str:
    return f"{preferences.persona_name} received your message: {message}"


async def execute_default_query(
    dataset_id: UUID,
    message: str,
) -> QueryResult:
    return {
        "columns": ["message"],
        "rows": [{"message": message}],
    }


async def execute_default_chart(
    dataset_id: UUID,
    message: str,
) -> ChartResult:
    return {
        "chart_type": "bar",
        "title": message,
        "labels": [],
        "series": [],
    }


def get_chat_message_workflow() -> ChatMessageWorkflow:
    """
    Creates the chat workflow with all required business dependencies.

    Composes the workflow by injecting the agent preferences workflow and
    the intent detector used during chat message processing.

    Returns:
        ChatMessageWorkflow:
            Fully configured chat workflow instance.
    """
    preferences_workflow = AgentPreferencesWorkflow()
    intent_detector = ChatIntentDetector()
    assistant = AssistantAdapter(execute_default_assistant)
    query_tool = QueryToolAdapter(execute_default_query)
    chart_tool = ChartToolAdapter(execute_default_chart)

    return ChatMessageWorkflow(
        preferences_workflow=preferences_workflow,
        intent_detector=intent_detector,
        assistant=assistant,
        query_tool=query_tool,
        chart_tool=chart_tool,
    )


def get_chat_message_service() -> ChatMessageService:
    """
    Creates the chat application service.

    Returns:
        ChatMessageService:
            Service configured with the chat workflow dependency.
    """
    workflow = get_chat_message_workflow()

    return ChatMessageService(
        workflow=workflow,
        logger=LOGGER,
    )


def get_chat_message_controller() -> ChatMessageController:
    """
    Creates the chat controller.

    Returns:
        ChatMessageController:
            Controller configured with the required service and logger
            dependencies.
    """
    service = get_chat_message_service()

    return ChatMessageController(
        service=service,
        logger=LOGGER,
    )
