from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from typing import Optional

from app.settings.setting import get_settings
from app.logs.setup_logger import LoggerManager, LOGGER


class JWTAuthenticator:
    """
    Handles JWT-based authentication for user access control.

    This class provides methods to create and verify JSON Web Tokens (JWT)
    using application-wide security settings. It supports configurable secret keys,
    algorithms, and expiration intervals.

    Attributes:
        secret_key (str): The secret key used to sign the JWT.
        algorithm (str): The algorithm used for JWT encoding and decoding.
        exp_minutes (int): Token expiration time in minutes.
        logger (LoggerManager): Logger instance for logging authentication actions.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        exp_minutes: Optional[int] = None,
        logger: Optional[LoggerManager] = None,
    ):
        settings = get_settings().security
        self.secret_key = secret_key or settings.secret_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.exp_minutes = exp_minutes or settings.jwt_exp_minutes
        self.logger = logger or LOGGER

    def create_access_token(self, subject: str) -> str:
        """
        Creates a signed JWT access token for a given subject.

        Args:
            subject (str): The subject identifier (typically the user ID or username).

        Returns:
            str: The encoded JWT access token as a string.
        """
        self.logger.log_info("[security] creating access token")
        self.logger.log_debug(
            f"[security] token payload: subject={subject}, exp_minutes={self.exp_minutes}"
        )
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.exp_minutes)
        to_encode = {"sub": str(subject), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        self.logger.log_debug(f"[security] token created: {encoded_jwt}")
        return encoded_jwt

    def verify_token(self, token: str) -> str:
        """
        Verifies a JWT access token and retrieves the subject.

        This method decodes and validates the JWT token. If valid, returns the subject (user ID).
        If the token is invalid or the subject is missing, an HTTPException is raised.

        Args:
            token (str): The JWT access token to be verified.

        Returns:
            int: The user ID (subject) extracted from the token.

        Raises:
            HTTPException: If the token is invalid, expired, or missing the subject.
        """
        self.logger.log_info("[security] verifying token")
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            self.logger.log_debug(f"[security] token decoded payload: {payload}")
            id: str = payload.get("sub")
            if id is None:
                self.logger.log_error("[security] token missing subject")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing subject.",
                )
            return int(id)

        except JWTError as e:
            self.logger.log_error(f"[security] JWT error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
