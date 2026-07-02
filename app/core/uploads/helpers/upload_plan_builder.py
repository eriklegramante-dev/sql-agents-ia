from math import ceil
from pathlib import Path
from uuid import UUID


class UploadPlanBuilder:
    """
    Helper responsible for building upload planning values.

    Attributes:
        None.
    """

    def normalize_dataset_name(self, dataset_name: str) -> str:
        """
        Normalize the dataset name by removing extra spaces.
        """
        return " ".join(dataset_name.strip().split())

    def generate_object_key(self, dataset_id: UUID, filename: str) -> str:
        """
        Generate the raw object key for blob storage.
        """
        safe_filename = Path(filename).name
        return f"datasets/{dataset_id}/raw/{safe_filename}"

    def calculate_chunks_count(
        self,
        file_size_bytes: int,
        chunk_size_bytes: int,
    ) -> int:
        """
        Calculate the expected amount of upload chunks.
        """
        return ceil(file_size_bytes / chunk_size_bytes)
