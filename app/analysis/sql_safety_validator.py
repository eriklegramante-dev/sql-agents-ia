import re


class SQLSafetyValidator:
    """
    Validates SQL queries before analytical execution.

    This validator ensures that only read-only SELECT statements are allowed
    to reach the analytical query adapter. It rejects empty queries, multiple
    SQL statements, and operations that may modify database objects or data.

    The implementation intentionally remains small and deterministic for the
    proof of concept. It does not execute SQL, access datasets, or depend on
    any database-specific infrastructure.

    Attributes:
        forbidden_keywords:
            SQL keywords representing operations that are not allowed in
            analytical read-only queries.
    """

    FORBIDDEN_KEYWORDS: frozenset[str] = frozenset(
        {
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "TRUNCATE",
        }
    )

    def validate(self, sql: str) -> str:
        """
        Validate and normalize a read-only analytical SQL query.

        The query must contain exactly one SQL statement and must begin with
        SELECT. Statements containing forbidden data-modification or
        schema-modification operations are rejected.

        A single trailing semicolon is accepted and removed during
        normalization.

        Args:
            sql:
                SQL query to validate.

        Returns:
            str:
                Normalized SQL query considered safe for analytical
                execution.

        Raises:
            ValueError:
                If the SQL query is empty, contains multiple statements,
                does not begin with SELECT, or contains a forbidden
                operation.
        """
        normalized_sql = self._normalize(sql)

        self._validate_single_statement(normalized_sql)
        self._validate_select_statement(normalized_sql)
        self._validate_forbidden_keywords(normalized_sql)

        return normalized_sql

    def _normalize(self, sql: str) -> str:
        """
        Normalize the SQL query before validation.

        Args:
            sql:
                Raw SQL query.

        Returns:
            str:
                SQL query without surrounding whitespace or a single
                trailing semicolon.

        Raises:
            ValueError:
                If the SQL query is empty.
        """
        normalized_sql = sql.strip()

        if not normalized_sql:
            raise ValueError("SQL query must not be empty.")

        if normalized_sql.endswith(";"):
            normalized_sql = normalized_sql[:-1].rstrip()

        if not normalized_sql:
            raise ValueError("SQL query must not be empty.")

        return normalized_sql

    def _validate_single_statement(
        self,
        sql: str,
    ) -> None:
        """
        Ensure that the query contains only one SQL statement.

        Args:
            sql:
                Normalized SQL query.

        Raises:
            ValueError:
                If an additional semicolon indicates multiple SQL
                statements.
        """
        if ";" in sql:
            raise ValueError("Multiple SQL statements are not allowed.")

    def _validate_select_statement(
        self,
        sql: str,
    ) -> None:
        """
        Ensure that the query is a read-only SELECT statement.

        Args:
            sql:
                Normalized SQL query.

        Raises:
            ValueError:
                If the query does not begin with SELECT.
        """
        if re.match(r"^SELECT\b", sql, flags=re.IGNORECASE) is None:
            raise ValueError("Only SELECT statements are allowed.")

    def _validate_forbidden_keywords(
        self,
        sql: str,
    ) -> None:
        """
        Reject SQL containing forbidden modification operations.

        Args:
            sql:
                Normalized SQL query.

        Raises:
            ValueError:
                If a forbidden SQL keyword is found.
        """
        for keyword in self.FORBIDDEN_KEYWORDS:
            pattern = rf"\b{re.escape(keyword)}\b"

            if re.search(pattern, sql, flags=re.IGNORECASE):
                raise ValueError(f"SQL operation '{keyword}' is not allowed.")
