from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner
from tests.e2e.helpers import build_cli_env


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def isolated_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    home = tmp_path / ".alphaxiv"
    monkeypatch.setenv("ALPHAXIV_HOME", str(home))
    return home


@pytest.fixture
def isolated_cli_env(isolated_home: Path) -> dict[str, str]:
    return build_cli_env(isolated_home)
