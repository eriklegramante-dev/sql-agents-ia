from enum import Enum


class UploadStatus(str, Enum):
    """Represents the upload lifecycle status."""

    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    PROFILING = "PROFILING"
    PROFILED = "PROFILED"
    FAILED = "FAILED"
    DELETED = "DELETED"


class DatasetStatus(str, Enum):
    """Represents the dataset lifecycle status."""

    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    PROFILING = "PROFILING"
    PROFILED = "PROFILED"
    FAILED = "FAILED"
    DELETED = "DELETED"
