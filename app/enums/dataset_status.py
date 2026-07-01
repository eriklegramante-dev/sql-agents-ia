from enum import Enum


class DatasetStatus(str, Enum):
    """Lifecycle states that control which dataset operations are allowed.

    The preparation workflow only accepts completed datasets and moves them
    through preparing, prepared, or failed states.
    """

    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    FAILED = "FAILED"
    DELETED = "DELETED"
