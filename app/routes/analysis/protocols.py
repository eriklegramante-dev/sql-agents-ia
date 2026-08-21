"""
Protocols and typing contracts for the analysis module.

Defines structural subtyping interfaces for persistence layers, query execution
adapters, and strongly-typed data transfer objects used across services.
"""

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums.dataset_status import DatasetStatus


class DatasetEntityProtocol(Protocol):
    """
    Structural interface representing the dataset domain entity.

    Exposes attributes strictly required by the analytical workflow.
    """

    id: UUID | str
    status: DatasetStatus
    table_name: str
    columns: list[str]


class QueryResult(BaseModel):
    """
    Structured response representation for analytical query execution.

    Attributes:
        columns (list[str]):
            List of column names returned by the query engine.
        rows (list[dict[str, object]]):
            List of row records mapped as column-to-value dictionaries.
    """

    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, object]] = Field(default_factory=list)


class DatasetRepositoryProtocol(Protocol):
    """
    Structural interface for dataset persistence management.

    Decouples domain and service logic from concrete database implementations.
    """

    async def find_by_id(self, dataset_id: UUID) -> DatasetEntityProtocol | None:
        """
        Retrieves a dataset entity by its unique identifier.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset.

        Returns:
            DatasetEntityProtocol | None:
                The typed dataset entity if found, otherwise None.
        """
        ...


class QueryAdapterProtocol(Protocol):
    """
    Structural interface for analytical query execution engines.

    Provides contract boundaries for executing analytical SQL statements.
    """

    async def execute_query(self, sql: str) -> QueryResult:
        """
        Executes an analytical read-only query statement.

        Args:
            sql (str):
                Sanitized analytical SQL query to run.

        Returns:
            QueryResult:
                Typed mapping containing returned column names and row values.
        """
        ...