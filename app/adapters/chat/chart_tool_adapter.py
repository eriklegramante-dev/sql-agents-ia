from collections.abc import Awaitable, Callable
from uuid import UUID

from app.chat.exceptions import ChartGenerationException
from app.chat.models import ChatArtifact, ChartResult

ChartExecutor = Callable[
    [UUID, str],
    Awaitable[ChartResult],
]


class ChartToolAdapter:
    """
    Adapts a chart-generation executor to the chat workflow.

    This adapter isolates chart-generation requests from the concrete
    visualization component responsible for creating graphical
    representations of analytical data. The injected executor may invoke an
    internal chart workflow, a visualization service, or another chart
    generation mechanism without exposing infrastructure details to the chat
    workflow.

    The adapter validates the generated chart result and converts it into
    the artifact format consumed by the chat workflow. Empty chart results
    are treated as predictable application failures and translated into
    ChartGenerationException. Unexpected programming errors are allowed to
    propagate without being hidden.

    Attributes:
        executor:
            Asynchronous callable responsible for generating structured chart
            data from a dataset identifier and a user request.
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
        """
        Generates a chart for the provided dataset and user request.

        Delegates the request to the injected chart executor, validates the
        generated result, and converts it into the artifact format consumed by
        the chat workflow.

        Args:
            dataset_id:
                Identifier of the dataset used to generate the chart.

            message:
                User message describing the requested chart.

        Returns:
            ChatArtifact:
                Structured artifact containing the generated chart data.

        Raises:
            ChartGenerationException:
                If the chart generation returns no result or cannot produce a
                valid chart artifact.
        """
        result = await self._executor(
            dataset_id,
            message,
        )

        if not result:
            raise ChartGenerationException("The chart generation returned no result.")

        return ChatArtifact(
            type="chart",
            content=result,
        )
