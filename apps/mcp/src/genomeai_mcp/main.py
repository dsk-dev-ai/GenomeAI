from __future__ import annotations

from genomeai_config import load_settings
from genomeai_logging import get_logger, setup_logging


def main() -> None:
    settings = load_settings()
    setup_logging(level=settings.log_level.value, name=settings.service_name)
    logger = get_logger(settings.service_name)
    logger.info("mcp server starting")

    try:
        from mcp.server.fastmcp import FastMCP

        server = FastMCP(
            "GenomeAI",
            instructions="GenomeAI MCP server for AI-assisted genomics analysis.",
        )
        logger.info("mcp server ready")
        server.run()
    except ImportError:
        logger.error("MCP SDK not available")
        raise


if __name__ == "__main__":
    main()
