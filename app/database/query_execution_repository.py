from uuid import UUID, uuid4

import asyncpg


class QueryExecutionRepository:
    """Persist completed analytical executions and count them by user.

    Each success record receives a new UUID. The calling workflow determines
    whether a query succeeded and checks dataset ownership before recording it.
    Counts are filtered by the supplied user identifier.

    Attributes:
        pool:
            Asynchronous PostgreSQL pool used to acquire connections.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        """Initialize execution persistence with an asynchronous pool.

        Args:
            pool: PostgreSQL pool used to acquire repository connections.
        """
        self.pool = pool

    async def record_success(
        self,
        *,
        user_id: int,
        dataset_id: UUID,
    ) -> None:
        """Insert one execution record using a newly generated identifier.

        The caller determines whether execution succeeded and checks dataset
        ownership. This method does not execute SQL analysis or deduplicate
        repeated queries.

        Args:
            user_id: Trusted user identifier associated with the execution.
            dataset_id: Identifier of the dataset used by the query.

        Returns:
            None after the insert completes.

        Raises:
            asyncpg.PostgresError: If PostgreSQL rejects or fails the insert.

        Pool acquisition failures also propagate to the caller.
        """
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO query_executions (id, user_id, dataset_id)
                VALUES ($1, $2, $3)
                """,
                uuid4(),
                user_id,
                dataset_id,
            )

    async def count_by_user(self, *, user_id: int) -> int:
        """Count execution records using a parameterized user filter.

        Args:
            user_id: User identifier used in the SQL ownership filter.

        Returns:
            Stored execution count converted to int, including zero.

        Raises:
            asyncpg.PostgresError: If PostgreSQL cannot execute the count.

        Pool acquisition failures also propagate; errors are not zero counts.
        """
        async with self.pool.acquire() as connection:
            count = await connection.fetchval(
                """
                SELECT COUNT(*)
                FROM query_executions
                WHERE user_id = $1
                """,
                user_id,
            )

        return int(count)