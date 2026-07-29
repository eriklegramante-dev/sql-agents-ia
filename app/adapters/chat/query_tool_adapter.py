from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from app.chat.exceptions import ChartGenerationException
from app.chat.models import ChatArtifact

ChartExecutor = Callable[
    [UUID, str],
    Awaitable[dict[str, Any]],
]


class ChartToolAdapter:
    """
    Adapts a chart-generation executor to the chat workflow.

    This adapter isolates chart requests from the concrete visualization
    component used by the application. The injected executor may call an
    existing chart workflow, visualization agent, or external chart service.

    The adapter converts the generated chart information into a ChatArtifact,
    ensuring that the workflow receives a stable domain structure regardless
    of the visualization technology used. Infrastructure failures are
    translated into a chat-specific domain exception.

    Attributes:
        executor:
            Asynchronous callable responsible for generating structured chart
            information from a dataset identifier and user request.
    """

    def __init__(
        self,
        executor: ChartExecutor,
    ) -> None:
        self._executor = executor

    async def execute(
        self,
        dataset_id: UUID,
        message: str,
    ) -> ChatArtifact:
        try:
            result = await self._executor(
                dataset_id,
                message,
            )
        except ChartGenerationException:
            raise
        except Exception as error:
            raise ChartGenerationException(
                "The requested chart could not be generated."
            ) from error

        if not result:
            raise ChartGenerationException(
                "The chart generator returned no result."
            )

        return ChatArtifact(
            type="chart",
            content=result,
        )