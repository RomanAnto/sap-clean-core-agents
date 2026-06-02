"""
SAP ABAP Accelerator — main.py
Entry point for the MCP server.
"""
import logging
import sys

from .server.fastmcp_server import ABAPAcceleratorServer
from .config.settings import load_config


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def main() -> None:
    try:
        config = load_config()
        setup_logging(config["server"].log_level)
        server = ABAPAcceleratorServer()
        server.run()
    except ValueError as exc:
        print(f"[ERROR] Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
