from app.adapters.storage.blob_storage_adapter import MultipartStorageAdapter
from app.routes.uploads.dtos.dto import UploadSignedPartDTO


class SignedPartsBuilder:
    """
    Helper responsible for generating signed upload URLs.

    Attributes:
        storage_adapter: Adapter used to generate signed part URLs.
    """

    def __init__(self, storage_adapter: MultipartStorageAdapter) -> None:
        self.storage_adapter = storage_adapter

    def build(
        self,
        object_key: str,
        upload_id: str,
        chunks_count: int,
    ) -> list[UploadSignedPartDTO]:
        """
        Generate signed upload URLs for all expected chunks.
        """
        return [
            UploadSignedPartDTO(
                part_number=part_number,
                upload_url=self.storage_adapter.generate_signed_part_url(
                    object_key=object_key,
                    upload_id=upload_id,
                    part_number=part_number,
                ),
            )
            for part_number in range(1, chunks_count + 1)
        ]
