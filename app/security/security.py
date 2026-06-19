from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database.repository import DatabaseRepository
from app.security.authenticator import JWTAuthenticator
from app.models.users_table import UserTable
from app.logs.setup_logger import LOGGER

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieves the current authenticated user based on the provided JWT access token.

    This dependency extracts and verifies the JWT token, fetches the user from the database,
    and raises an HTTPException if authentication fails or the user does not exist.

    Args:
        token (str): JWT access token extracted from the request's Authorization header.

    Returns:
        UserTable: The authenticated user object.

    Raises:
        HTTPException: If the token is invalid, expired, or the user is not found.
    """
    LOGGER.log_info("[security] extracting current user from token")
    authenticator = JWTAuthenticator()
    repository = DatabaseRepository(model=UserTable)
    try:
        id = authenticator.verify_token(token)
        LOGGER.log_debug(f"[security] authenticated user: {id}")
        user = await repository.get_by_id(id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        return user

    except Exception as e:
        LOGGER.log_error(f"[security] invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
