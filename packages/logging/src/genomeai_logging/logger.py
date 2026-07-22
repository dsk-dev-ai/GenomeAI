from __future__ import annotations

import logging
import sys
from typing import TextIO


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    stream: TextIO | None = None,
) -> None:
    logger = logging.getLogger("genomeai")
    logger.setLevel(level.upper())

    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setLevel(level.upper())

    if json_format:

        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                import json

                return json.dumps(
                    {
                        "timestamp": self.formatTime(record),
                        "level": record.levelname,
                        "name": record.name,
                        "message": record.getMessage(),
                    }
                )

        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )

    logger.addHandler(handler)


def setup_logging(level: str, name: str = "genomeai") -> None:
    configure_logging(level=level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"genomeai.{name}")
