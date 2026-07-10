class StorageOperationError(RuntimeError):
    """Exception raised when an object storage operation fails.

    Attributes:
        operation: Storage operation that could not be completed.

    Args:
        operation: Name of the failed storage operation.
    """

    def __init__(self, operation: str) -> None:
        """Initialize the storage operation error.

        Args:
            operation: Name of the failed storage operation.
        """
        self.operation = operation
        super().__init__(f"Storage operation failed: {operation}.")
