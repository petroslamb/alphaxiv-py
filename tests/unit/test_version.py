from __future__ import annotations

from importlib.metadata import version

from alphaxiv import __version__
from alphaxiv._version import PACKAGE_NAME, USER_AGENT


def test_runtime_version_matches_package_metadata() -> None:
    assert __version__ == version(PACKAGE_NAME)


def test_user_agent_includes_runtime_version() -> None:
    assert f"{PACKAGE_NAME}/{__version__}" == USER_AGENT
