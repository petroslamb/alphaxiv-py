"""Package version helpers."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

PACKAGE_NAME = "alphaxiv-py"

try:
    __version__ = version(PACKAGE_NAME)
except PackageNotFoundError:
    __version__ = "0.0.0+local"

USER_AGENT = f"{PACKAGE_NAME}/{__version__}"
