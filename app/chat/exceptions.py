from app.prepare.exceptions import AppException


class ChatException(AppException):
    """
    Base exception for predictable chat processing errors.
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
    """Signals a generic failure while generating an assistant response."""

    def __init__(
        self,
        message: str = "The assistant could not generate a response.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_type="assistant_execution_error",
        )


class AssistantUnavailableException(ChatException):
    """Signals that the external assistant service is temporarily unavailable."""

    def __init__(
        self,
        message: str = "The assistant service is temporarily unavailable.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_type="assistant_unavailable",
        )


class AssistantTimeoutException(ChatException):
    """Signals that the external assistant service timed out."""

    def __init__(
        self,
        message: str = "The assistant service took too long to respond.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=504,
            error_type="assistant_timeout",
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