from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DatasetPreviewRequestDTO(BaseModel):
    """Represents the request for dataset preview retrieval."""

    dataset_id: UUID = Field(
        ...,
        description="Unique identifier of the dataset.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of rows returned in the preview.",
    )

    @field_validator("limit", mode="before")
    @classmethod
    def normalize_limit(cls, value: Any) -> int:
        if value is None or value == "":
            return 20

        return int(value)


class DatasetPreviewResponseDataDTO(BaseModel):
    """Represents the dataset preview response payload."""

    model_config = ConfigDict(populate_by_name=True)

    dataset_id: UUID
    status: str
    limit: int
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    rows_count: int
    returned_rows_count: int


class DatasetPreviewResponseDTO(BaseModel):
    """Represents the standard API response for dataset preview retrieval."""

    success: bool
    message: str
    data: DatasetPreviewResponseDataDTO | None = None
    errors: list[Any] | None = None