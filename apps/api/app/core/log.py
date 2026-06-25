import logging
import sys


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT, stream=sys.stdout)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
