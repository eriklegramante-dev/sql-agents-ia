import re

FORBIDDEN_SQL_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|EXEC|ATTACH|DETACH|COPY)\b",
    re.IGNORECASE,
)


def validate_read_only_select(sql: str) -> None:
    """
    Validates that a given SQL query is strictly a read-only analytical statement.

    Ensures that the statement starts with SELECT or WITH and does not contain
    any forbidden data mutation or administrative operation keywords.

    Args:
        sql:
            SQL statement string to validate.

    Raises:
        ValueError:
            If the query does not begin with an analytical SELECT/WITH statement
            or contains forbidden SQL keywords.
    """
    cleaned = sql.strip().rstrip(";")
    if not cleaned.upper().startswith("SELECT") and not cleaned.upper().startswith(
        "WITH"
    ):
        raise ValueError("Only analytical SELECT queries are allowed.")
    if FORBIDDEN_SQL_PATTERNS.search(cleaned):
        raise ValueError(
            "Forbidden SQL operation detected. Only read-only SELECT is permitted."
        )
