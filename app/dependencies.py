import sys
from pathlib import Path

from iduconfig import Config
from loguru import logger

from app.common.api_handler.api_handler import APIHandler

logger.remove()
log_level = "INFO"
log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <b>{message}</b>"
logger.add(sys.stderr, format=log_format, level=log_level, colorize=True)

config = Config()
log_path = Path().absolute() / config.get("LOG_FILE")

logger.add(
    log_path,
    format=log_format,
    level="INFO",
)

urban_api_handler = APIHandler(config.get("URBAN_API"))
