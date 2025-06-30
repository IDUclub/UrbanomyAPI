import sys

from loguru import logger
from iduconfig import Config

from app.common.api_handler.api_handler import APIHandler

logger.remove()
log_level = "INFO"
log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <b>{message}</b>"
logger.add(
    sys.stderr,
    format=log_format,
    level=log_level,
    colorize=True
)

logger.add("urbanomy.log", level=log_level, format=log_format, colorize=False, backtrace=True, diagnose=True)

config = Config()

logger.add(
    "urbanomy.log",
    format=log_format,
    level="INFO",
)

urban_api_handler = APIHandler(config.get("URBAN_API"))
