"""Automation toolkit for booking VFS France appointments."""

from .bot import VFSFranceBot, BookingError
from .config import load_config, Config

__all__ = [
    "VFSFranceBot",
    "BookingError",
    "load_config",
    "Config",
]
