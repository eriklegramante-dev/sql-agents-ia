import pytest
from pydantic import ValidationError

from app.routes.uploads.dto import UploadInitRequestDTO


def test_upload_init_request_rejects_blank_dataset_name() -> None:
    with pytest.raises(ValidationError):
        UploadInitRequestDTO(
            filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1000,
            dataset_name="   ",
            description=None,
        )