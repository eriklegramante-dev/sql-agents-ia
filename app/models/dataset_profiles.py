import uuid

from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database.base import Base


class DatasetProfileTable(Base):
    """
    SQLAlchemy model responsible for persisting dataset profiling metadata.

    This model belongs to the persistence layer and maps the
    ``dataset_profiles`` table used by the dataset profiling workflow. Each
    record stores the analytical profile generated from a prepared dataset,
    allowing the application to retrieve profiling information without
    recalculating statistics from the prepared Parquet file.

    The profile is stored as JSONB and is associated with a single dataset
    through a one-to-one relationship.

    Attributes:
        id (UUID):
            Unique identifier of the persisted profile record.
        dataset_id (UUID):
            Identifier of the dataset that owns the generated profile.
        profile (JSONB):
            Serialized profiling metadata, including row and column counts,
            column classifications, null summaries, cardinality summaries,
            basic statistics, quality warnings, and optional preview samples.
        created_at (datetime):
            Timestamp indicating when the profile record was created.
        updated_at (datetime):
            Timestamp of the most recent profile update.
    """

    __tablename__ = "dataset_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    profile = Column(JSONB, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )