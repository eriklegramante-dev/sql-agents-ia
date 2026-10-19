class UploadCompletionError(RuntimeError):
    """Exception raised when an upload cannot be completed in storage.

    Attributes:
        None.

    Args:
        None.
    """

class UploadAccessDeniedError(PermissionError):
    """Signal that the trusted caller does not own the requested upload.

    Raised by completion and abort workflows before storage operations when
    the persisted owner does not match the supplied user identifier.
    """
