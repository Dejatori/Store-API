"""
Logging configuration module for the Store API application.
This module configures loggers, handlers, formatters and filters
for comprehensive application logging including console, file
and external service outputs.
"""
# https://docs.python.org/3/howto/logging.html#logging-flow
import logging
from logging.config import dictConfig

from storeapi.config import DevConfig, config


def obfuscated(email: str, obfuscated_length: int):
    """Obfuscate email address for logging purposes."""
    if not email:
        return email
    try:
        local_part, domain_part = email.split("@")
        obfuscated_local_part = local_part[:obfuscated_length] + "*" * (
            len(local_part) - obfuscated_length
        )
        return f"{obfuscated_local_part}@{domain_part}"
    except ValueError:
        # If the email is not valid, return it as is
        return email


class EmailObfuscationFilter(logging.Filter):
    """
    Logging filter that obfuscates email addresses in log records.

    This filter examines log records for email fields and applies
    obfuscation to protect user privacy while maintaining diagnostic value.
    The obfuscation level is configurable depending on the environment.
    """
    def __init__(self, name: str = "", obfuscated_length: int = 2) -> None:
        super().__init__(name)
        self.obfuscated_length = obfuscated_length

    def filter(self, record: logging.LogRecord) -> bool:
        if "email" in record.__dict__:
            record.email = obfuscated(record.email, self.obfuscated_length)
        return True


handlers = ["default", "rotating_file"]
if config.ENV_STATE == "prod":
    handlers = ["default", "rotating_file", "logtail"]


def configure_logging() -> None:
    """
    Configure application-wide logging settings.

    Sets up different logging handlers (console, file, external services),
    formatters with correlation IDs, and specific logger configurations
    for various components. The configuration adapts based on the current
    environment (development/production).
    """
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if isinstance(config, DevConfig) else 32,
                    "default_value": "-",
                },
                "email_obfuscation": {
                    "()": EmailObfuscationFilter,
                    "obfuscated_length": 2 if isinstance(config, DevConfig) else 0,
                },
            },
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s",
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": "%(levelprefix)s (%(correlation_id)s) %(client_addr)s - "
                    "%(request_line)s - %(status_code)s",
                    "use_colors": True,
                },
                "file": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s %(msecs)03d %(levelname)s "
                    "%(correlation_id)s %(name)s %(lineno)d %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id", "email_obfuscation"],
                },
                "access": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "access",
                    "filters": ["correlation_id", "email_obfuscation"],
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filters": ["correlation_id", "email_obfuscation"],
                    "filename": "storeapi.log",
                    "maxBytes": 1024 * 1024 * 5,  # 5 MB
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
                "logtail": {
                    # https://betterstack.com/docs/logs/python/
                    "class": "logtail.LogtailHandler",
                    "level": "INFO",
                    "formatter": "file",
                    "filters": ["correlation_id", "email_obfuscation"],
                    "source_token": config.LOGTAIL_API_KEY,
                    "host": config.LOGTAIL_INGESTING_HOST,
                },
            },
            "loggers": {
                "storeapi": {
                    "handlers": handlers,
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "propagate": False,  # Prevents double logging
                },
                "uvicorn.access": {
                    "handlers": ["access", "rotating_file"],
                    "level": "INFO",
                },
                "databases": {"handlers": ["default"], "level": "WARNING"},
                "aiosqlite": {"handlers": ["default"], "level": "WARNING"},
            },
        },
    )
