from __future__ import annotations

import asyncio
import signal

from genomeai_config import load_settings
from genomeai_logging import get_logger, setup_logging


class Worker:
    def __init__(self) -> None:
        settings = load_settings()
        setup_logging(level=settings.log_level.value, name=settings.service_name)
        self._logger = get_logger(settings.service_name)
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        self._logger.info("worker starting")
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)
        await self._shutdown_event.wait()
        self._logger.info("worker stopped")

    def _handle_shutdown(self) -> None:
        self._logger.info("shutdown signal received")
        self._shutdown_event.set()


def main() -> None:
    worker = Worker()
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
