import uuid

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database.base import Base


class ColumnSchema(BaseModel):
    """
    Data transfer model representing the inferred schema of a single dataset
    column.

    This model is produced during the dataset preparation workflow after the
    uploaded tabular data has been analyzed. It contains the normalized column
    name, the original source column name, the inferred logical data type,
    nullability information, representative sample values, and optional
    conversion warnings.

    The model is used both for schema persistence and for serializing the
    dataset preparation response returned by the API.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="Normalized column name.")
    original_name: str = Field(..., description="Original column name in the source file.")
    data_type: str = Field(
        ...,
        validation_alias=AliasChoices("data_type", "type"),
        serialization_alias="type",
        description="Inferred logical data type.",
    )
    nullable: bool = Field(..., description="Whether the column contains null values.")
    sample_values: list[str] = Field(
        default_factory=list,
        exclude=True,
        description="Representative non-null values from the prepared column.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        exclude=True,
        description="Conversion warnings produced while preparing the column.",
    )


class DatasetSchemaTable(Base):
    """
    SQLAlchemy model responsible for persisting inferred dataset schemas.

    This model belongs to the persistence layer and maps the
    ``dataset_schemas`` table used by the preparation workflow. Each record
    stores the inferred schema generated from a prepared dataset, allowing the
    application to retrieve column metadata without reprocessing the original
    file.

    The schema is stored as JSON and is associated with a single dataset
    through a one-to-one relationship.

    Attributes:
        id (UUID):
            Unique identifier of the persisted schema record.
        dataset_id (UUID):
            Identifier of the dataset that owns the inferred schema.
        columns (JSONB):
            Serialized collection of inferred column definitions.
        created_at (datetime):
            Timestamp indicating when the schema record was created.
        updated_at (datetime):
            Timestamp of the most recent schema update.
    """

    __tablename__ = "dataset_schemas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    columns = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
