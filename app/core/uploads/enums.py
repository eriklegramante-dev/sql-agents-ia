from enum import StrEnum


class UploadStatus(StrEnum):
    """Represents the upload lifecycle status."""

    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    FAILED = "FAILED"


class DatasetStatus(StrEnum):
    """Represents the dataset lifecycle status."""

    UPLOADING = "UPLOADING"
    AVAILABLE = "AVAILABLE"
    ABORTED = "ABORTED"
    FAILED = "FAILED"