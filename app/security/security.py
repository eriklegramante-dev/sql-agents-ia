from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.settings.setting import get_settings
from app.logs.setup_logger import LOGGER


def verify_signature(x_signature: str = Header(...)):
    """
    Verifies if the provided signature matches the fixed signature in the environment.

    Args:
        x_signature (str): Signature provided in the request header.

    Raises:
        HTTPException: Returns a 401 status code if the signature is invalid.
    """
    if x_signature != get_settings().security.secret_key:
        LOGGER.log_error("[security] Unauthorized access attempt: Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    LOGGER.log_info("[security] Signature successfully verified")


def get_trusted_user_id(
    x_user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    _signature: Annotated[None, Depends(verify_signature)],
) -> int:
    """Read the user identity supplied by a trusted internal caller.

    The caller must authenticate the user before forwarding their ID and
    internal signature. The signature is a shared secret; this dependency
    does not validate an end-user token or bind the signature to the ID.

    Args:
        x_user_id: Positive user identifier supplied in X-User-Id.
        _signature: Result of the internal signature dependency.

    Returns:
        User identifier supplied by the trusted caller.

    Raises:
        HTTPException: If the signature dependency rejects the request.
    """
    return x_user_id