from datetime import datetime
from typing import Any, Optional


class ResponseBuilder:
    """Creates the standard success and error response envelope.

    Includes the success flag, message, optional data, errors, and UTC timestamp
    for endpoints that use the shared response shape.
    """

    @staticmethod
    def success(
        message: str,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build a successful response envelope.

        Args:
            message (str): Human-readable success message.
            data (Optional[dict[str, Any]]): Optional response payload.

        Returns:
            dict[str, Any]: Response with ``success=True``, message, data,
            no errors, and an ISO UTC timestamp.
        """
        return {
            "success": True,
            "message": message,
            "data": data,
            "errors": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def error(
        message: str,
        errors: Optional[list[str]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build an error response envelope.

        Args:
            message (str): Human-readable error message.
            errors (Optional[list[str]]): Optional error detail messages.
            data (Optional[dict[str, Any]]): Optional payload to include with
                the error response.

        Returns:
            dict[str, Any]: Response with ``success=False``, message, data,
            error details, and an ISO UTC timestamp.
        """
        return {
            "success": False,
            "message": message,
            "data": data,
            "errors": errors or [],
            "timestamp": datetime.utcnow().isoformat(),
        }
