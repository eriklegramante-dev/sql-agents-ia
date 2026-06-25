from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.enums.dataset_status import DatasetStatus


class DatasetTable(BaseModel):
    """Represents a dataset row stored in the database.

    Keeps upload status, raw/prepared object keys, row and column counts, and
    audit timestamps used by the preparation workflow.
    """

    id: UUID
    name: str
    status: DatasetStatus
    raw_object_key: str
    prepared_object_key: Optional[str] = None
    rows_count: Optional[int] = None
    columns_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
