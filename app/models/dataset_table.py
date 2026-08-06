import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base


class DatasetStatus(enum.Enum):
    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    PROFILING = "PROFILING"
    PROFILED = "PROFILED"
    FAILED = "FAILED"
    DELETED = "DELETED"


class DatasetTable(Base):
    """
    SQLAlchemy model that represents dataset metadata persisted in the database.

    Stores the dataset lifecycle status, raw and prepared object keys, row and
    column counters, processing error information, and audit timestamps used by
    the dataset preparation workflow.
    """

    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=True)
    
    status = Column(
        Enum(DatasetStatus, name="dataset_status"),
        nullable=False,
        default=DatasetStatus.UPLOADING,
    )
    raw_object_key = Column(Text, nullable=False)
    prepared_object_key = Column(Text, nullable=True)
    
    user_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=True)
    file_type = Column(String(100), nullable=True)
    content_type = Column(String(100), nullable=True)    
    file_size_bytes = Column(Integer, nullable=True)
    current_upload_job_id = Column(String(255), nullable=True)
    
    rows_count = Column(Integer, nullable=True)
    columns_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
