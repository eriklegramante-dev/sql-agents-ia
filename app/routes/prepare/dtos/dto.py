from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.dataset_schema_table import ColumnSchema


class DatasetPreparationResponseData(BaseModel):
    """Structured result returned by the preparation workflow.

    Exposes dataset metadata, prepared object location, inferred schema, and
    updated counters for controller serialization.

    Attributes:
        dataset_id (UUID): Identifier of the prepared dataset.
        status (str): Current dataset status value after preparation.
        raw_object_key (str): Storage key of the original uploaded file.
        prepared_object_key (Optional[str]): Storage key of the generated
            prepared Parquet file.
        rows_count (Optional[int]): Number of rows in the prepared DataFrame.
        columns_count (Optional[int]): Number of columns in the prepared
            DataFrame.
        columns_schema (list[ColumnSchema]): Inferred schema metadata,
            serialized as ``schema`` in API responses.
        updated_at (datetime): Last update timestamp for the dataset record.
    """

    model_config = ConfigDict(populate_by_name=True)

    dataset_id: UUID
    status: str
    raw_object_key: str
    prepared_object_key: Optional[str]
    rows_count: Optional[int]
    columns_count: Optional[int]
    columns_schema: list[ColumnSchema] = Field(serialization_alias="schema")
    updated_at: datetime
