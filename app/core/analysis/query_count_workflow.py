from app.core.analysis.contracts import QueryExecutionCounter


class QueryCountWorkflow:
    """Workflow responsible for retrieving a user's successful query count.

    Delegates counting to the injected repository using the trusted identity
    provided by the calling layer. Repository failures propagate to the caller.

    Attributes:
        repository:
            Repository contract used to count persisted query executions.
    """

    def __init__(self, repository: QueryExecutionCounter) -> None:
        """Initialize the count workflow with its repository contract.

        Args:
            repository: Repository responsible for counting stored executions.
        """
        self.repository = repository

    async def execute(self, *, user_id: int) -> int:
        """Retrieve the successful execution count for the trusted user.

        Args:
            user_id: User identifier supplied by the trusted route dependency.

        Returns:
            Stored execution count, including zero when no records exist.

        Repository failures propagate without substituting a zero count.
        """
        return await self.repository.count_by_user(user_id=user_id)