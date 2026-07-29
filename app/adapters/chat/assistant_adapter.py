from collections.abc import Awaitable, Callable

from app.chat.exceptions import AssistantExecutionException
from app.chat.models import ChatPreferences

AssistantExecutor = Callable[
    [str, ChatPreferences],
    Awaitable[str],
]


class AssistantAdapter:
    """
    Adapts an external assistant executor to the chat workflow.

    This adapter isolates the chat domain from the implementation used to
    generate conversational responses. The injected executor may communicate
    with an LLM provider, an internal agent, or another response-generation
    service without exposing infrastructure details to the workflow.

    The adapter validates the generated response and translates unexpected
    infrastructure failures into a chat-specific domain exception.

    Attributes:
        executor:
            Asynchronous callable responsible for generating the assistant
            response from the user message and effective chat preferences.
    """

    def __init__(
        self,
        executor: AssistantExecutor,
    ) -> None:
        self._executor = executor

    async def execute(
        self,
        message: str,
        preferences: ChatPreferences,
    ) -> str:
        try:
            answer = await self._executor(
                message,
                preferences,
            )
        except AssistantExecutionException:
            raise
        except Exception as error:
            raise AssistantExecutionException(
                "The assistant could not generate a response."
            ) from error

        normalized_answer = answer.strip()

        if not normalized_answer:
            raise AssistantExecutionException(
                "The assistant returned an empty response."
            )

        return normalized_answer