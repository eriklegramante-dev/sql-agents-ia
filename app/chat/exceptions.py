from app.prepare.exceptions import AppException


class ChatException(AppException):
    """
    Base exception for predictable chat processing errors.

    Carries the HTTP response information required by the chat controller
    while keeping chat-specific failures grouped under a single exception
    hierarchy.

    Args:
        message:
            Human-readable error message returned to the client.
        status_code:
            HTTP status code associated with the chat error.
        error_type:
            Stable machine-readable chat error category.
        details:
            Optional validation or diagnostic information.

    Attributes:
        message:
            Human-readable error message.
        status_code:
            HTTP status code used in the response.
        error_type:
            Machine-readable chat error category.
        details:
            Additional error details, empty when omitted.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_type: str | None = None,
        details: list[str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_type=error_type,
            details=details,
        )


class AssistantExecutionException(ChatException):
    """Signals a failure while generating an assistant response."""

    def __init__(
        self,
        message: str = "The assistant could not generate a response.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_type="assistant_execution_error",
        )


class QueryExecutionException(ChatException):
    """Signals a failure while executing an analytical query."""

    def __init__(
        self,
        message: str = "The analytical query could not be executed.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_type="query_execution_error",
        )


class ChartGenerationException(ChatException):
    """Signals a failure while generating a chart."""

    def __init__(
        self,
        message: str = "The requested chart could not be generated.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_type="chart_generation_error",
        )