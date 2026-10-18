from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import asyncpg

from app.adapters.chat.assistant_adapter import AssistantAdapter
from app.adapters.chat.chart_tool_adapter import ChartToolAdapter
from app.adapters.chat.query_tool_adapter import QueryToolAdapter
from app.chat.dependencies import (
    get_chat_message_controller,
    get_chat_message_service,
    get_chat_message_workflow,
)
from app.chat.intent_detector import ChatIntentDetector
from app.core.agent_preferences.workflow import AgentPreferencesWorkflow
from app.core.chat.workflow import ChatMessageWorkflow
from app.routes.chat.controllers.controller import ChatMessageController
from app.routes.chat.services.service import ChatMessageService


def create_fake_pool() -> asyncpg.Pool:
    return MagicMock(spec=asyncpg.Pool)


def create_fake_settings():
    return SimpleNamespace(
        openai=SimpleNamespace(
            api_key="test-key",
            model="gpt-5.6-luna",
        )
    )


def test_get_chat_message_workflow_returns_chat_message_workflow():
    pool = create_fake_pool()

    fake_executor = MagicMock()

    with (
        patch(
            "app.chat.dependencies.get_settings",
            return_value=create_fake_settings(),
        ),
        patch(
            "app.chat.dependencies.create_openai_assistant_executor",
            return_value=fake_executor,
        ) as mocked_factory,
    ):
        workflow = get_chat_message_workflow(pool)

    assert isinstance(workflow, ChatMessageWorkflow)
    assert isinstance(
        workflow._preferences_workflow,
        AgentPreferencesWorkflow,
    )
    assert isinstance(
        workflow._intent_detector,
        ChatIntentDetector,
    )
    assert isinstance(
        workflow._assistant,
        AssistantAdapter,
    )
    assert isinstance(
        workflow._query_tool,
        QueryToolAdapter,
    )
    assert isinstance(
        workflow._chart_tool,
        ChartToolAdapter,
    )

    assert workflow._preferences_workflow.repository.pool is pool

    mocked_factory.assert_called_once_with(
        api_key="test-key",
        model="gpt-5.6-luna",
    )

    assert workflow._assistant._executor is fake_executor


def test_get_chat_message_service_returns_chat_message_service():
    pool = create_fake_pool()

    with (
        patch(
            "app.chat.dependencies.get_settings",
            return_value=create_fake_settings(),
        ),
        patch(
            "app.chat.dependencies.create_openai_assistant_executor",
            return_value=MagicMock(),
        ),
    ):
        service = get_chat_message_service(pool)

    assert isinstance(service, ChatMessageService)
    assert isinstance(
        service._workflow,
        ChatMessageWorkflow,
    )


def test_get_chat_message_controller_returns_chat_message_controller():
    pool = create_fake_pool()

    with (
        patch(
            "app.chat.dependencies.get_settings",
            return_value=create_fake_settings(),
        ),
        patch(
            "app.chat.dependencies.create_openai_assistant_executor",
            return_value=MagicMock(),
        ),
    ):
        controller = get_chat_message_controller(pool)

    assert isinstance(controller, ChatMessageController)
    assert isinstance(
        controller._service,
        ChatMessageService,
    )