from fastapi import Header, HTTPException

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