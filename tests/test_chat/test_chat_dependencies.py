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


def test_get_chat_message_workflow_returns_chat_message_workflow():
    workflow = get_chat_message_workflow()

    assert isinstance(workflow, ChatMessageWorkflow)
    assert isinstance(workflow._preferences_workflow, AgentPreferencesWorkflow)
    assert isinstance(workflow._intent_detector, ChatIntentDetector)


def test_get_chat_message_service_returns_chat_message_service():
    service = get_chat_message_service()

    assert isinstance(service, ChatMessageService)
    assert isinstance(service._workflow, ChatMessageWorkflow)


def test_get_chat_message_controller_returns_chat_message_controller():
    controller = get_chat_message_controller()

    assert isinstance(controller, ChatMessageController)
    assert isinstance(controller._service, ChatMessageService)
