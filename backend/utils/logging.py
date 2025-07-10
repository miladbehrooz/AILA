import sys
from loguru import logger
from backend.settings import settings


def setup_logger():

    logger.remove()
    logger.add(sys.stdout, level="INFO")

    logger.add(
        settings.LOG_FILE_PATH,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
    )

    return logger


logger = setup_logger()
