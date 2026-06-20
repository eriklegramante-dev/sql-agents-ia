from enum import Enum


class UploadStatus(str, Enum):
    """Represents the upload lifecycle status."""

    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    FAILED = "FAILED"


class DatasetStatus(str, Enum):
    """Represents the dataset lifecycle status."""

    UPLOADING = "UPLOADING"
    AVAILABLE = "AVAILABLE"
    ABORTED = "ABORTED"
    FAILED = "FAILED"