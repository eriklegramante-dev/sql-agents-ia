"""
SQL security validator module.

Ensures incoming analytical SQL statements are strictly read-only SELECT
operations and rejects destructive DDL, DML, or injection patterns.
"""

import re

DANGEROUS_SQL_PATTERNS = [
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE)\b",
    r"\b(GRANT|REVOKE|EXEC|EXECUTE|DECLARE|CALL)\b",
    r";",
    r"--",
    r"/\*.*?\*/",
]


def validate_safe_select_query(sql: str) -> None:
    """
    Validates that a given SQL statement is a safe, read-only SELECT query.

    Args:
        sql (str):
            The raw SQL string to validate.

    Raises:
        ValueError:
            If the query is empty, does not start with SELECT, or contains
            forbidden SQL commands/mutations.
    """
    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    cleaned_sql = sql.strip()

    if not re.match(r"^SELECT\b", cleaned_sql, re.IGNORECASE):
        raise ValueError("Only read-only SELECT queries are allowed.")

    for pattern in DANGEROUS_SQL_PATTERNS:
        if re.search(pattern, cleaned_sql, re.IGNORECASE):
            raise ValueError(
                "Unsafe SQL detected: Query contains forbidden statements or characters."
            )
