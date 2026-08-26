from uuid import UUID

from app.prepare.exceptions import ProcessingException


class DatasetRelatedRecordsDeletionException(ProcessingException):
    """Signals failure while removing persistence records for a dataset.

    Args:
        dataset_id:
            Unique identifier of the dataset whose related records
            could not be removed.
    """

    def __init__(
        self,
        dataset_id: UUID,
    ) -> None:
        super().__init__(f"Failed to delete related records for dataset {dataset_id}.")
