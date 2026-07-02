from pathlib import Path

from app.logs.setup_logger import LOGGER
from app.settings.setting import UploadSettings


class UploadValidator:
    """
    Helper responsible for validating upload request constraints.

    Attributes:
        config: Upload settings used to validate file size limits.
        allowed_extensions: File extensions accepted for upload initialization.
        accepted_content_types: MIME types accepted for upload initialization.
    """

    def __init__(self, config: UploadSettings) -> None:
        self.config = config
        self.allowed_extensions = {".csv", ".xlsx"}
        self.accepted_content_types = {
            "text/csv",
            "application/csv",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

    def validate(self, filename: str, content_type: str, file_size_bytes: int) -> None:
        """
        Validates all upload request constraints before initialization.

        This method coordinates the validation process by checking the file
        extension, MIME type, and file size against the configured upload
        restrictions.

        Args:
            filename (str):
                Name of the uploaded file.
            content_type (str):
                MIME type informed by the upload request.
            file_size_bytes (int):
                Size of the uploaded file in bytes.

        Raises:
            ValueError:
                If any upload validation rule is violated.
        """
        self._validate_file_extension(filename)
        self._validate_content_type(content_type)
        self._validate_file_size(file_size_bytes)

    def _validate_file_extension(self, filename: str) -> None:
        """
        Validates whether the uploaded file extension is supported.

        Args:
            filename (str):
                Name of the uploaded file.

        Raises:
            ValueError:
                If the file extension is not one of the supported formats.
        """
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            LOGGER.log_warning(
                f"[upload:init:validator] Invalid file extension: {extension}"
            )
            raise ValueError("Invalid file extension. Allowed: csv, xlsx.")

    def _validate_content_type(self, content_type: str) -> None:
        """
        Validates whether the uploaded file MIME type is supported.

        Args:
            content_type (str):
                MIME type informed by the upload request.

        Raises:
            ValueError:
                If the MIME type is not supported.
        """
        if content_type not in self.accepted_content_types:
            LOGGER.log_warning(
                f"[upload:init:validator] Invalid content type: {content_type}"
            )
            raise ValueError("Invalid content type for upload.")

    def _validate_file_size(self, file_size_bytes: int) -> None:
        """
        Validates whether the uploaded file size is within the configured limit.

        Args:
            file_size_bytes (int):
                Size of the uploaded file in bytes.

        Raises:
            ValueError:
                If the uploaded file exceeds the maximum allowed size.
        """
        if file_size_bytes > self.config.max_upload_size_bytes:
            LOGGER.log_warning(
                "[upload:init:validator] File size exceeds limit: "
                f"file_size_bytes={file_size_bytes}, "
                f"max_upload_size_bytes={self.config.max_upload_size_bytes}"
            )
            raise ValueError("File size exceeds the maximum upload limit.")