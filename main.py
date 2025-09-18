"""Command line interface for the VFS France booking automation."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from vfsbot import BookingError, VFSFranceBot, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automate VFS France appointment booking")
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the YAML configuration file",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the browser in headless mode",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    config = load_config(args.config)
    # CLI flag overrides the YAML file for convenience
    config.webdriver.headless = args.headless or config.webdriver.headless

    bot = VFSFranceBot(config)
    try:
        bot.run()
    except BookingError as exc:
        logging.getLogger("vfsbot").error("Booking failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
