from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from app.chat.exceptions import QueryExecutionException
from app.chat.models import ChatArtifact

QueryExecutor = Callable[
    [UUID, str],
    Awaitable[dict[str, Any]],
]


class QueryToolAdapter:
    """
    Adapts an analytical query executor to the chat workflow.

    This adapter isolates dataset-question processing from the concrete
    component responsible for generating and executing analytical queries.
    The injected executor may call an existing query workflow, SQL agent, or
    another analytical service.

    The adapter converts the raw execution result into a ChatArtifact,
    providing a stable result structure for the chat workflow. Infrastructure
    failures are translated into a chat-specific domain exception.

    Attributes:
        executor:
            Asynchronous callable responsible for processing an analytical
            question against the selected dataset and returning structured
            query results.
    """

    def __init__(
        self,
        executor: QueryExecutor,
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
        except QueryExecutionException:
            raise
        except Exception as error:
            raise QueryExecutionException(
                "The analytical query could not be executed."
            ) from error

        if not result:
            raise QueryExecutionException(
                "The analytical query returned no result."
            )

        return ChatArtifact(
            type="query_result",
            content=result,
        )