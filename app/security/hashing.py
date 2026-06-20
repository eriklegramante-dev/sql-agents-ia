from typing import Optional
from passlib.context import CryptContext

from app.logs.setup_logger import LoggerManager, LOGGER


class PasswordManager:
    """
    Manages password hashing and verification using bcrypt.

    This class provides utilities for securely hashing plaintext passwords
    and verifying password hashes, leveraging the passlib CryptContext.
    It supports customizable logging.

    Attributes:
        logger (LoggerManager): Logger instance for security-related messages.
        pwd_context (CryptContext): Context for hashing and verifying passwords.
    """

    def __init__(self, logger: Optional[LoggerManager] = None) -> None:
        self.logger = logger or LOGGER
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """
        Hashes a plaintext password using bcrypt.

        Args:
            password (str): The plaintext password to hash.

        Returns:
            str: The resulting hashed password.
        """
        self.logger.log_info("[security] hashing password")
        hashed = self.pwd_context.hash(password)
        self.logger.log_debug("[security] password hashed")
        return hashed

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plaintext password against a hashed password.

        Args:
            plain_password (str): The user's plaintext password.
            hashed_password (str): The hashed password to compare against.

        Returns:
            bool: True if the password matches the hash, False otherwise.

        Raises:
            Exception: Any exception encountered during verification is logged and False is returned.
        """
        self.logger.log_info("[security] verifying password")
        try:
            is_valid = self.pwd_context.verify(plain_password, hashed_password)
            self.logger.log_debug(
                f"[security] password verification result: {is_valid}"
            )
            return is_valid

        except Exception as e:
            self.logger.log_error(f"[security] error verifying password: {e}")
            return False
