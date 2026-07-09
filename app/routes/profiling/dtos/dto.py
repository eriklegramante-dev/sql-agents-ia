from uuid import UUID

from pydantic import BaseModel, Field


class DatasetProfileRequestDTO(BaseModel):
    """Request DTO for dataset profiling."""

    dataset_id: UUID = Field(
        ...,
        description="Unique identifier of the dataset to profile.",
    )


class DatasetProfileColumnDTO(BaseModel):
    """Profiling information for a dataset column."""

    name: str
    type: str
    nullable: bool
    null_count: int
    null_percentage: float
    cardinality: int
    statistics: dict = Field(default_factory=dict)


class NullSummaryDTO(BaseModel):
    """Summary of dataset null values."""

    total_nulls: int
    columns_with_nulls: int


class CardinalitySummaryDTO(BaseModel):
    """Summary of dataset column cardinality."""

    high_cardinality_columns: list[str] = Field(default_factory=list)
    low_cardinality_columns: list[str] = Field(default_factory=list)


class DatasetProfileResponseDataDTO(BaseModel):
    """Response payload containing dataset profiling results."""

    dataset_id: UUID
    status: str
    rows_count: int
    columns_count: int
    columns: list[DatasetProfileColumnDTO]
    nulls_summary: NullSummaryDTO
    cardinality_summary: CardinalitySummaryDTO
    basic_statistics: dict = Field(default_factory=dict)
    quality_warnings: list[str] = Field(default_factory=list)
    updated_at: str


class DatasetProfileResponseDTO(BaseModel):
    """Standard response DTO for the dataset profiling endpoint."""

    success: bool
    message: str
    data: DatasetProfileResponseDataDTO