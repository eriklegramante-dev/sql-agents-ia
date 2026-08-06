from collections.abc import Awaitable, Callable
from uuid import UUID

from app.chat.exceptions import QueryExecutionException
from app.chat.models import ChatArtifact, QueryResult


QueryExecutor = Callable[
    [UUID, str],
    Awaitable[QueryResult],
]


class QueryToolAdapter:
    """
    Adapts an analytical query executor to the chat workflow.

    This adapter isolates dataset-question processing from the concrete
    component responsible for generating and executing analytical queries.
    It receives the executor through dependency injection, validates the
    structured result, and converts it into the artifact format consumed by
    the chat workflow.

    An empty query result is treated as a predictable application failure and
    translated into QueryExecutionException. Unexpected programming errors
    are allowed to propagate without being hidden.

    Attributes:
        executor:
            Asynchronous callable responsible for processing analytical
            questions against a dataset.
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
        """
        Executes an analytical query for the provided dataset and user message.

        Delegates the request to the injected query executor, validates the
        returned result, and converts it into the artifact format consumed by
        the chat workflow.

        Args:
            dataset_id:
                Identifier of the dataset against which the analytical query
                should be executed.

            message:
                User message containing the analytical question.

        Returns:
            ChatArtifact:
                Structured artifact containing the analytical query result.

        Raises:
            QueryExecutionException:
                If the query execution returns no result or cannot produce a
                valid analytical response.
        """
        result = await self._executor(
            dataset_id,
            message,
        )

        if not result:
            raise QueryExecutionException(
                "The analytical query returned no result."
            )

        return ChatArtifact(
            type="query_result",
            content=result,
        )