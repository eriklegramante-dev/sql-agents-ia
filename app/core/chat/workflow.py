from app.chat.intent_detector import ChatIntentDetector
from app.chat.models import (
    ChatIntent,
    ChatMessageInput,
    ChatMessageResult,
    ChatPreferences,
)
from app.core.agent_preferences.workflow import AgentPreferencesWorkflow


class ChatMessageWorkflow:
    """
    Orchestrates the business flow for processing chat messages.

    This workflow coordinates the retrieval of user preferences, intent
    detection, and response generation for incoming chat messages. It keeps
    business decisions isolated from the HTTP, service, persistence, and
    infrastructure layers.

    Dependencies are received through constructor injection. The workflow
    does not create its own collaborators, which reduces coupling and makes
    each dependency replaceable during tests or future implementations.

    The current implementation identifies the message intent and returns a
    temporary response for each supported flow. Assistant, analytical query,
    and chart-generation adapters can be integrated later without changing
    the route, controller, or service responsibilities.

    Attributes:
        preferences_workflow:
            Workflow responsible for retrieving the effective preferences
            associated with the requesting user. When persisted preferences
            are unavailable, that workflow provides the configured fallback
            profile.

        intent_detector:
            Component responsible for classifying the incoming message as
            general chat, dataset question, chart request, or unsupported
            request.
    """

    def __init__(
        self,
        preferences_workflow: AgentPreferencesWorkflow,
        intent_detector: ChatIntentDetector,
    ) -> None:
        self._preferences_workflow = preferences_workflow
        self._intent_detector = intent_detector

    async def execute(
        self,
        request: ChatMessageInput,
    ) -> ChatMessageResult:
        raw_preferences = self._preferences_workflow.execute(
            request.user_id,
        )

        preferences = self._build_preferences(raw_preferences)
        intent = self._intent_detector.detect(request.message)

        answer = self._build_temporary_answer(
            message=request.message,
            intent=intent,
            preferences=preferences,
        )

        return ChatMessageResult(
            user_id=request.user_id,
            session_id=request.session_id,
            answer=answer,
            intent=intent,
            tool_used=None,
            dataset_id=request.dataset_id,
            artifact=None,
        )

    def _build_preferences(
        self,
        raw_preferences: dict[str, object],
    ) -> ChatPreferences:
        return ChatPreferences(
            persona_name=str(
                raw_preferences.get(
                    "persona_name",
                    "Data Assistant",
                )
            ),
            persona_description=str(
                raw_preferences.get(
                    "persona_description",
                    "Assistant specialized in data analysis.",
                )
            ),
            response_style=str(
                raw_preferences.get(
                    "response_style",
                    "clear and concise",
                )
            ),
            language=str(
                raw_preferences.get(
                    "language",
                    "en",
                )
            ),
            tool_preferences=tuple(
                value
                for value in raw_preferences.get(
                    "tool_preferences",
                    [],
                )
                if isinstance(value, str)
            ),
            guardrails=tuple(
                value
                for value in raw_preferences.get(
                    "guardrails",
                    [],
                )
                if isinstance(value, str)
            ),
        )

    def _build_temporary_answer(
        self,
        message: str,
        intent: ChatIntent,
        preferences: ChatPreferences,
    ) -> str:
        if intent == ChatIntent.UNSUPPORTED:
            return "This request is not supported by the assistant."

        if intent == ChatIntent.CHART_REQUEST:
            return (
                "The chart request was identified and will be processed "
                "using the chart generation tool."
            )

        if intent == ChatIntent.DATASET_QUESTION:
            return (
                "The dataset question was identified and will be processed "
                "using the analytical query tool."
            )

        return (
            f"{preferences.persona_name} received your message: "
            f"{message}"
        )