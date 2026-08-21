from collections.abc import Iterable

from app.adapters.chat.assistant_adapter import AssistantAdapter
from app.adapters.chat.chart_tool_adapter import ChartToolAdapter
from app.adapters.chat.query_tool_adapter import QueryToolAdapter
from app.chat.exceptions import (
    AssistantExecutionException,
    ChartGenerationException,
    QueryExecutionException,
)
from app.chat.intent_detector import ChatIntentDetector
from app.chat.models import (
    ChatArtifact,
    ChatIntent,
    ChatMessageInput,
    ChatMessageResult,
    ChatPreferences,
)
from app.core.agent_preferences.workflow import AgentPreferencesWorkflow


class ChatMessageWorkflow:
    """
    Orchestrates the business flow for processing chat messages.

    This workflow retrieves the effective user preferences, detects the
    incoming message intent, and delegates execution to the appropriate
    injected adapter.

    General chat messages are processed by the assistant adapter. Analytical
    dataset questions are delegated to the query tool adapter, while chart
    requests are delegated to the chart tool adapter. Unsupported requests
    receive a clear response describing the capabilities available in the
    current proof of concept.

    Dataset-dependent requests require a dataset identifier. When none is
    provided, the workflow returns a clarification response without invoking
    an analytical tool.

    All dependencies are received through constructor injection. The workflow
    does not instantiate concrete collaborators, which keeps the orchestration
    testable and decoupled from infrastructure implementations.

    Args:
        preferences_workflow:
            Workflow responsible for retrieving persisted user preferences or
            returning the configured fallback profile.

        intent_detector:
            Component responsible for classifying incoming messages into the
            supported chat intents.

        assistant:
            Adapter responsible for generating responses to general chat
            messages.

        query_tool:
            Adapter responsible for executing analytical dataset questions.

        chart_tool:
            Adapter responsible for generating chart artifacts.

    Attributes:
        preferences_workflow:
            Injected workflow used to retrieve effective user preferences.

        intent_detector:
            Injected component used to classify chat messages.

        assistant:
            Injected adapter used for general chat responses.

        query_tool:
            Injected adapter used for analytical query execution.

        chart_tool:
            Injected adapter used for chart generation.
    """

    def __init__(
        self,
        preferences_workflow: AgentPreferencesWorkflow,
        intent_detector: ChatIntentDetector,
        assistant: AssistantAdapter,
        query_tool: QueryToolAdapter,
        chart_tool: ChartToolAdapter,
    ) -> None:
        self._preferences_workflow = preferences_workflow
        self._intent_detector = intent_detector
        self._assistant = assistant
        self._query_tool = query_tool
        self._chart_tool = chart_tool

    async def execute(
        self,
        request: ChatMessageInput,
    ) -> ChatMessageResult:
        """
        Processes an incoming chat message.

        Retrieves the effective user preferences, detects the message intent,
        delegates execution to the corresponding adapter, and returns the
        standardized workflow result.

        Args:
            request:
                Validated chat message input containing the user identifier,
                message, optional dataset identifier, session identifier, and
                contextual metadata.

        Returns:
            ChatMessageResult:
                Structured result containing the final answer, detected
                intent, selected tool, optional dataset identifier, and
                optional generated artifact.

        Raises:
            ValueError:
                If the agent preferences workflow receives an invalid user
                identifier.

            AssistantExecutionException:
                If the assistant cannot generate a valid response.

            QueryExecutionException:
                If the analytical query executor cannot produce a valid
                result.

            ChartGenerationException:
                If the chart executor cannot produce a valid chart result.
        """
        raw_preferences = self._preferences_workflow.execute(
            request.user_id,
        )

        preferences = self._build_preferences(raw_preferences)
        intent = self._intent_detector.detect(request.message)

        if intent == ChatIntent.GENERAL_CHAT:
            return await self._handle_general_chat(
                request=request,
                preferences=preferences,
            )

        if intent == ChatIntent.DATASET_QUESTION:
            return await self._handle_dataset_question(request)

        if intent == ChatIntent.CHART_REQUEST:
            return await self._handle_chart_request(request)

        return self._handle_unsupported_request(request)

    async def _handle_general_chat(
        self,
        request: ChatMessageInput,
        preferences: ChatPreferences,
    ) -> ChatMessageResult:
        answer = await self._assistant.execute(
            message=request.message,
            preferences=preferences,
        )

        return self._build_result(
            request=request,
            answer=answer,
            intent=ChatIntent.GENERAL_CHAT,
            tool_used=None,
            artifact=None,
        )

    async def _handle_dataset_question(
        self,
        request: ChatMessageInput,
    ) -> ChatMessageResult:
        if request.dataset_id is None:
            return self._build_result(
                request=request,
                answer=(
                    "A dataset must be selected before an analytical "
                    "question can be processed."
                ),
                intent=ChatIntent.DATASET_QUESTION,
                tool_used=None,
                artifact=None,
            )

        artifact = await self._query_tool.execute(
            dataset_id=request.dataset_id,
            message=request.message,
        )

        return self._build_result(
            request=request,
            answer="The analytical query was executed successfully.",
            intent=ChatIntent.DATASET_QUESTION,
            tool_used="query",
            artifact=artifact,
        )

    async def _handle_chart_request(
        self,
        request: ChatMessageInput,
    ) -> ChatMessageResult:
        if request.dataset_id is None:
            return self._build_result(
                request=request,
                answer=(
                    "A dataset must be selected before a chart can be " "generated."
                ),
                intent=ChatIntent.CHART_REQUEST,
                tool_used=None,
                artifact=None,
            )

        artifact = await self._chart_tool.execute(
            dataset_id=request.dataset_id,
            message=request.message,
        )

        return self._build_result(
            request=request,
            answer="The requested chart was generated successfully.",
            intent=ChatIntent.CHART_REQUEST,
            tool_used="chart",
            artifact=artifact,
        )

    def _handle_unsupported_request(
        self,
        request: ChatMessageInput,
    ) -> ChatMessageResult:
        return self._build_result(
            request=request,
            answer=(
                "This request is not supported. The current chat can answer "
                "general questions, analyze a selected dataset, and generate "
                "charts."
            ),
            intent=ChatIntent.UNSUPPORTED,
            tool_used=None,
            artifact=None,
        )

    def _build_result(
        self,
        request: ChatMessageInput,
        answer: str,
        intent: ChatIntent,
        tool_used: str | None,
        artifact: ChatArtifact | None,
    ) -> ChatMessageResult:
        return ChatMessageResult(
            user_id=request.user_id,
            session_id=request.session_id,
            answer=answer,
            intent=intent,
            tool_used=tool_used,
            dataset_id=request.dataset_id,
            artifact=artifact,
        )

    def _build_preferences(
        self,
        raw_preferences: dict[str, object],
    ) -> ChatPreferences:
        return ChatPreferences(
            persona_name=self._get_string_value(
                raw_preferences,
                key="persona_name",
                default="Data Assistant",
            ),
            persona_description=self._get_string_value(
                raw_preferences,
                key="persona_description",
                default="Assistant specialized in data analysis.",
            ),
            response_style=self._get_string_value(
                raw_preferences,
                key="response_style",
                default="clear and concise",
            ),
            language=self._get_string_value(
                raw_preferences,
                key="language",
                default="en",
            ),
            tool_preferences=self._get_string_tuple(
                raw_preferences.get("tool_preferences"),
            ),
            guardrails=self._get_string_tuple(
                raw_preferences.get("guardrails"),
            ),
        )

    def _get_string_value(
        self,
        values: dict[str, object],
        key: str,
        default: str,
    ) -> str:
        value = values.get(key)

        if isinstance(value, str) and value.strip():
            return value

        return default

    def _get_string_tuple(
        self,
        value: object,
    ) -> tuple[str, ...]:
        if not isinstance(value, Iterable) or isinstance(value, str):
            return ()

        return tuple(item for item in value if isinstance(item, str))
