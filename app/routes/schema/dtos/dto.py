from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatasetSchemaRequestDTO(BaseModel):
    """Represents the request for dataset schema retrieval.

    Contains the dataset identifier validated before the request reaches
    the controller, service, and workflow layers.
    """

    dataset_id: UUID = Field(
        ...,
        description="Unique identifier of the dataset.",
    )


class DatasetSchemaColumnDTO(BaseModel):
    """Represents the inferred schema information for a dataset column.

    Includes the column name, inferred data type, nullability, safe sample
    values, and any warnings generated during schema inference.
    """

    name: str
    original_name: str | None = None
    type: str
    nullable: bool | None = None
    sample_values: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DatasetSchemaResponseDataDTO(BaseModel):
    """Represents the payload returned by the dataset schema retrieval route.

    Contains dataset metadata and the persisted inferred schema associated
    with the requested dataset.
    """

    model_config = ConfigDict(populate_by_name=True)

    dataset_id: UUID
    status: str
    schema_columns: list[DatasetSchemaColumnDTO] = Field(
        default_factory=list,
        alias="schema",
    )
    columns_count: int
    updated_at: datetime | None = None


class DatasetSchemaResponseDTO(BaseModel):
    """Represents the standard API response for dataset schema retrieval.

    Wraps the operation result, response message, and schema payload following
    the application's response pattern.
    """

    success: bool
    message: str
    data: DatasetSchemaResponseDataDTO | None = None
    errors: list[str] | None = None
