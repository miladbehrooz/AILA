import sys
from loguru import logger
from backend.settings import settings


def setup_logger() -> logger:
    """Configure the global Loguru logger for console and file output.
    Returns:
        logger: Configured Loguru logger instance.
    """

    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        enqueue=True,
    )

    logger.add(
        settings.LOG_FILE_PATH,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,
    )

    return logger


logger = setup_logger()
