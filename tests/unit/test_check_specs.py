from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_checker():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_specs.py"
    spec = importlib.util.spec_from_file_location("check_specs", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_valid_scaffold(root: Path) -> None:
    (root / "specs" / "features").mkdir(parents=True)
    (root / "specs" / "templates").mkdir(parents=True)
    (root / "specs" / "templates" / "feature-spec-template.md").write_text(
        "# Template\n",
        encoding="utf-8",
    )
    (root / "specs" / "README.md").write_text(
        "# Specs\n\n[Example](features/example.md)\n",
        encoding="utf-8",
    )
    (root / "specs" / "features" / "example.md").write_text(
        "\n".join(
            [
                "# Example",
                "",
                "## Status",
                "",
                "Status: Implemented",
                "",
                "## Endpoint Evidence",
                "",
                "- `GET /example` is confirmed in docs.",
                "",
                "## Acceptance Criteria",
                "",
                "- Users can read examples.",
                "",
                "## Validation Commands",
                "",
                "```bash",
                "uv run pytest",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_current_repo_specs_pass() -> None:
    checker = _load_checker()
    root = Path(__file__).resolve().parents[2]

    assert checker.check_specs(root) == []


def test_valid_scaffold_passes(tmp_path: Path) -> None:
    checker = _load_checker()
    _write_valid_scaffold(tmp_path)

    assert checker.check_specs(tmp_path) == []


def test_missing_required_feature_section_fails(tmp_path: Path) -> None:
    checker = _load_checker()
    _write_valid_scaffold(tmp_path)
    feature = tmp_path / "specs" / "features" / "example.md"
    feature.write_text(
        "# Example\n\n"
        "## Status\n\n"
        "Status: Implemented\n\n"
        "## Endpoint Evidence\n\n"
        "- `GET /example`\n\n"
        "## Validation Commands\n\n"
        "uv run pytest\n",
        encoding="utf-8",
    )

    messages = [error.message for error in checker.check_specs(tmp_path)]

    assert "specs/features/example.md is missing ## Acceptance Criteria" in messages


def test_stale_index_link_fails(tmp_path: Path) -> None:
    checker = _load_checker()
    _write_valid_scaffold(tmp_path)
    (tmp_path / "specs" / "README.md").write_text(
        "# Specs\n\n[Missing](features/missing.md)\n",
        encoding="utf-8",
    )

    messages = [error.message for error in checker.check_specs(tmp_path)]

    assert "specs/README.md does not link features/example.md" in messages
    assert "specs/README.md links missing features/missing.md" in messages


def test_validation_commands_require_uv_run(tmp_path: Path) -> None:
    checker = _load_checker()
    _write_valid_scaffold(tmp_path)
    feature = tmp_path / "specs" / "features" / "example.md"
    feature.write_text(feature.read_text(encoding="utf-8").replace("uv run pytest", "pytest"))

    messages = [error.message for error in checker.check_specs(tmp_path)]

    assert "specs/features/example.md validation commands must include a uv run command" in messages
