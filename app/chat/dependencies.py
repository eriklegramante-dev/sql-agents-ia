from app.core.agent_preferences.workflow import AgentPreferencesWorkflow
from app.core.chat.workflow import ChatMessageWorkflow
from app.routes.chat.controllers.controller import ChatMessageController
from app.routes.chat.services.service import ChatMessageService
from app.chat.intent_detector import ChatIntentDetector


def get_chat_message_workflow() -> ChatMessageWorkflow:
    preferences_workflow = AgentPreferencesWorkflow()
    intent_detector = ChatIntentDetector()

    return ChatMessageWorkflow(
        preferences_workflow=preferences_workflow,
        intent_detector=intent_detector,
    )


def get_chat_message_service() -> ChatMessageService:
    workflow = get_chat_message_workflow()

    return ChatMessageService(
        workflow=workflow,
    )


def get_chat_message_controller() -> ChatMessageController:
    service = get_chat_message_service()

    return ChatMessageController(
        service=service,
    )