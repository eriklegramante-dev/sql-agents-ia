from uuid import UUID

import asyncpg
from fastapi import Depends

from app.adapters.chat.assistant_adapter import AssistantAdapter
from app.adapters.chat.chart_tool_adapter import ChartToolAdapter
from app.adapters.chat.openai_assistant_executor import (
    create_openai_assistant_executor,
)
from app.adapters.chat.query_tool_adapter import QueryToolAdapter
from app.agents.repository import AgentPreferencesRepository
from app.chat.intent_detector import ChatIntentDetector
from app.chat.models import ChartResult, QueryResult
from app.core.agent_preferences.workflow import AgentPreferencesWorkflow
from app.core.chat.workflow import ChatMessageWorkflow
from app.database.connection import get_db_pool
from app.logs.setup_logger import LOGGER
from app.routes.chat.controllers.controller import ChatMessageController
from app.routes.chat.services.service import ChatMessageService
from app.settings.setting import get_settings


async def execute_default_query(
    dataset_id: UUID,
    message: str,
) -> QueryResult:
    """
    Execute the temporary analytical query implementation.

    This executor provides a temporary query result used by the dependency
    composition layer until the analytical query engine is integrated.

    Args:
        dataset_id:
            Identifier of the dataset selected for analysis.

        message:
            Analytical question submitted by the user.

    Returns:
        QueryResult:
            Temporary structured query result.
    """
    return {
        "columns": ["message"],
        "rows": [{"message": message}],
    }


async def execute_default_chart(
    dataset_id: UUID,
    message: str,
) -> ChartResult:
    """
    Generate the temporary chart implementation.

    This executor provides a temporary chart result used by the dependency
    composition layer until the chart generation engine is integrated.

    Args:
        dataset_id:
            Identifier of the dataset selected for visualization.

        message:
            User request describing the desired chart.

    Returns:
        ChartResult:
            Temporary structured chart result.
    """
    return {
        "chart_type": "bar",
        "title": message,
        "labels": [],
        "series": [],
    }


def get_chat_message_workflow(
    pool: asyncpg.Pool,
) -> ChatMessageWorkflow:
    """
    Create the chat workflow with all required business dependencies.

    Resolves application configuration in the composition layer and injects
    the required OpenAI configuration into the assistant executor.

    Args:
        pool:
            Shared asynchronous PostgreSQL connection pool.

    Returns:
        ChatMessageWorkflow:
            Fully configured chat workflow instance.
    """
    settings = get_settings()

    repository = AgentPreferencesRepository(pool)
    preferences_workflow = AgentPreferencesWorkflow(repository)

    intent_detector = ChatIntentDetector()

    openai_executor = create_openai_assistant_executor(
        api_key=settings.openai.api_key,
        model=settings.openai.model,
    )

    assistant = AssistantAdapter(openai_executor)

    query_tool = QueryToolAdapter(execute_default_query)
    chart_tool = ChartToolAdapter(execute_default_chart)

    return ChatMessageWorkflow(
        preferences_workflow=preferences_workflow,
        intent_detector=intent_detector,
        assistant=assistant,
        query_tool=query_tool,
        chart_tool=chart_tool,
    )


def get_chat_message_service(
    pool: asyncpg.Pool,
) -> ChatMessageService:
    """
    Create the chat application service.

    Args:
        pool:
            Shared asynchronous PostgreSQL connection pool.

    Returns:
        ChatMessageService:
            Service configured with the chat workflow dependency.
    """
    workflow = get_chat_message_workflow(pool)

    return ChatMessageService(
        workflow=workflow,
        logger=LOGGER,
    )


def get_chat_message_controller(
    pool: asyncpg.Pool = Depends(get_db_pool),  # noqa: B008
) -> ChatMessageController:
    """
    Create the chat controller.

    Args:
        pool:
            Shared asynchronous PostgreSQL connection pool provided
            by FastAPI dependency injection.

    Returns:
        ChatMessageController:
            Controller configured with the required service and logger
            dependencies.
    """
    service = get_chat_message_service(pool)

    return ChatMessageController(
        service=service,
        logger=LOGGER,
    )