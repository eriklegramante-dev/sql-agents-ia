from typing import Optional


class AppException(Exception):
    """Base exception for predictable application errors.

    Carries the message, HTTP status code, error type, and optional details
    consumed by route handlers when building error responses.

    Args:
        message (str): Human-readable error message returned to the client.
        status_code (int): HTTP status code associated with the error.
        error_type (Optional[str]): Stable machine-readable error category.
        details (Optional[list[str]]): Additional validation or diagnostic
            messages returned in the error response.

    Attributes:
        message (str): Human-readable error message.
        status_code (int): HTTP status code to use in the route response.
        error_type (Optional[str]): Machine-readable error category.
        details (list[str]): Additional error details, empty when omitted.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_type: Optional[str] = None,
        details: Optional[list[str]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or []
        super().__init__(message)


class ValidationException(AppException):
    """Signals invalid request or domain data that should return HTTP 400.

    Args:
        message (str): Validation failure message.
        details (Optional[list[str]]): Field-level or rule-level validation
            details to include in the response.
    """

    def __init__(self, message: str, details: Optional[list[str]] = None):
        super().__init__(message, 400, "validation_error", details)


class NotFoundException(AppException):
    """Signals a missing resource that should return HTTP 404.

    Args:
        message (str): Missing resource message.
    """

    def __init__(self, message: str):
        super().__init__(message, 404, "not_found")


class ConflictException(AppException):
    """Signals a state conflict, such as preparing an ineligible dataset.

    Args:
        message (str): Conflict message.
        details (Optional[list[str]]): Additional conflict details.
    """

    def __init__(self, message: str, details: Optional[list[str]] = None):
        super().__init__(message, 409, "conflict", details)


class StorageException(AppException):
    """Signals storage read/write failures that should return HTTP 500.

    Args:
        message (str): Storage failure message.
    """

    def __init__(self, message: str):
        super().__init__(message, 500, "storage_error")


class ProcessingException(AppException):
    """Signals non-storage processing failures that should return HTTP 500.

    Args:
        message (str): Processing failure message.
    """

    def __init__(self, message: str):
        super().__init__(message, 500, "processing_error")
