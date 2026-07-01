import logging
import sys
from pathlib import Path
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from app.logs.trace import get_trace_id
from app.settings.setting import Environment, Settings, get_settings

LOGS_DIRECTORY = Path("logs")
LOG_FILE_PATH = LOGS_DIRECTORY / "app.log"


class LoggerManager:
    """
    LoggerManager provides a centralized logging utility with support for trace ids,
    configurable debug mode, and Sentry integration for error tracking.

    Attributes:
        settings: Application settings object, loaded from configuration.
        debug (bool): Flag to enable or disable debug logging and Sentry integration.
        logger (logging.Logger): The logger instance used for logging messages.
    """

    def __init__(
        self, debug: bool = False, settings: Optional[Settings] = None
    ) -> None:
        self.settings = settings or get_settings()
        self.debug = debug
        self.logger = logging.getLogger("logger")
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        if not self._has_handler("console"):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.set_name("console")
            console_handler.setLevel(logging.DEBUG if self.debug else logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        if not self._has_handler("file"):
            LOGS_DIRECTORY.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
            file_handler.set_name("file")
            file_handler.setLevel(logging.DEBUG if self.debug else logging.INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        if not self.debug:
            sentry_logging = LoggingIntegration(
                level=logging.INFO, event_level=logging.ERROR
            )
            sentry_sdk.init(
                dsn=self.settings.sentry.dns,
                default_integrations=False,
                integrations=[sentry_logging],
                send_default_pii=True,
                traces_sample_rate=1.0,
            )

    def _has_handler(self, name: str) -> bool:
        return any(handler.get_name() == name for handler in self.logger.handlers)

    def log_info(self, message: str) -> None:
        """
        Logs an info-level message with the optional trace id context.

        Args:
            message (str): The message to be logged.
        """
        trace = get_trace_id()
        log_message = f"trace id: {trace} - {message}" if trace else message
        self.logger.info(log_message)

    def log_debug(self, message: str) -> None:
        """
        Logs a debug-level message with the optional trace id context.

        Args:
            message (str): The debug message to be logged.
        """
        if self.debug:
            trace = get_trace_id()
            debug_message = f"trace id: {trace} - {message}" if trace else message
            self.logger.debug(debug_message)

    def log_error(self, message: str) -> None:
        """
        Logs an error-level message with the optional trace id context
        and sends the error message to Sentry if debug mode is disabled.

        Args:
            message (str): The error message to be logged and reported.
        """
        trace = get_trace_id()
        error_message = f"trace id: {trace} - {message}" if trace else message
        self.logger.error(error_message)
        if not self.debug:
            sentry_sdk.capture_message(error_message, level="error")

    def log_warning(self, message: str) -> None:
        """
        Logs an warning-level message with the optional trace id context
        and sends the warning message to Sentry if debug mode is disabled.

        Args:
            message (str): The waning message to be logged and reported.
        """
        trace = get_trace_id()
        waning_message = f"trace id: {trace} - {message}" if trace else message
        self.logger.warning(waning_message)
        if not self.debug:
            sentry_sdk.capture_message(waning_message, level="warning")


ENV = get_settings().env.environment
DEBUG_FLAG = ENV == Environment.DEV

LOGGER = LoggerManager(debug=DEBUG_FLAG)
