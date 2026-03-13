"""Filesystem paths used by the CLI."""

from __future__ import annotations

import os
from pathlib import Path

ALPHAXIV_HOME_ENV = "ALPHAXIV_HOME"


def get_home_path() -> Path:
    """Return the base config directory."""
    home = os.environ.get(ALPHAXIV_HOME_ENV)
    if home:
        return Path(home).expanduser()
    return Path.home() / ".alphaxiv"


def get_context_path() -> Path:
    """Return the CLI context file path."""
    return get_home_path() / "context.json"


def get_assistant_context_path() -> Path:
    """Return the CLI assistant context file path."""
    return get_home_path() / "assistant-context.json"


def get_api_key_path() -> Path:
    """Return the saved API key file path."""
    return get_home_path() / "api-key.json"


def ensure_home_path() -> Path:
    """Create and return the base config directory."""
    path = get_home_path()
    path.mkdir(parents=True, exist_ok=True)
    return path
