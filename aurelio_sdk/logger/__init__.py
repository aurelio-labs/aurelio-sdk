import logging
import os
from typing import NoReturn, cast

import colorlog


class CustomLogger(logging.Logger):
    def error_raise(self, message: str) -> NoReturn:
        self.error(message)
        raise


class CustomFormatter(colorlog.ColoredFormatter):
    def __init__(self):
        super().__init__(
            "%(log_color)s[AurelioSDK] %(asctime)s %(levelname)s %(filename)s:%(lineno)d|%(funcName)s(): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            reset=True,
            style="%",
        )


class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/health") == -1


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.classname = (
            record.name.split(".")[-1] if "." in record.name else record.name
        )
        record.funcname = record.funcName
        return True


def setup_custom_logger(name: str) -> CustomLogger:
    log_level = os.getenv("LOG_LEVEL", "INFO")
    if log_level == "DEBUG":
        level = logging.DEBUG
    elif log_level == "INFO":
        level = logging.INFO
    elif log_level == "WARNING":
        level = logging.WARNING
    elif log_level == "ERROR":
        level = logging.ERROR
    elif log_level == "CRITICAL":
        level = logging.CRITICAL
    else:
        level = logging.INFO
    logging.setLoggerClass(CustomLogger)
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format=(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - "
            "%(funcName)s() - %(message)s"
        ),
    )
    logger = cast(CustomLogger, logging.getLogger(name))
    logger.handlers = []
    formatter = CustomFormatter()
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addFilter(HealthCheckFilter())
    logger.addFilter(ContextFilter())
    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())
    logger.setLevel(level)
    logger.propagate = False
    return logger


logger: CustomLogger = setup_custom_logger(__name__)


__all__ = ["logger"]
