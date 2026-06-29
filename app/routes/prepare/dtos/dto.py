from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.dataset_schema_table import ColumnSchema


class DatasetPreparationRequestDTO(BaseModel):
    """
    Request DTO responsible for validating the dataset identifier received by the
    dataset preparation endpoint.
    """

    model_config = ConfigDict(extra="forbid")

    dataset_id: UUID = Field(
        ...,
        description="Unique identifier of the dataset to prepare.",
    )


class DatasetPreparationDataDTO(BaseModel):
    """
    Response data returned after a successful dataset preparation.

    Contains the updated dataset metadata, storage information,
    generated schema, row and column statistics.
    """

    model_config = ConfigDict(populate_by_name=True)

    dataset_id: UUID = Field(..., description="Identifier of the prepared dataset.")
    status: str = Field(..., description="Current dataset status after preparation.")
    raw_object_key: str = Field(
        ...,
        description="Storage key of the original uploaded file.",
    )
    prepared_object_key: Optional[str] = Field(
        None,
        description="Storage key of the generated prepared Parquet file.",
    )
    rows_count: Optional[int] = Field(
        None,
        description="Number of rows in the prepared dataset.",
    )
    columns_count: Optional[int] = Field(
        None,
        description="Number of columns in the prepared dataset.",
    )
    columns_schema: list[ColumnSchema] = Field(
        default_factory=list,
        validation_alias=AliasChoices("columns_schema", "schema"),
        serialization_alias="schema",
        description="Inferred schema metadata serialized as schema in responses.",
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp of the dataset metadata.",
    )


class DatasetPreparationResponseDTO(BaseModel):
    """
    Success response envelope returned after dataset preparation.

    Contains the operation status, a human-readable message, and the prepared
    dataset payload when the operation succeeds. Error responses are built by
    the route handler and include their own ``errors`` field.
    """

    success: bool = Field(..., description="Indicates if the operation was successful.")
    message: Optional[str] = Field(
        None,
        description="Contextual message for the operation.",
    )
    data: Optional[DatasetPreparationDataDTO] = Field(
        None,
        description="Dataset preparation result data.",
    )


DatasetPreparationResponseData = DatasetPreparationDataDTO
