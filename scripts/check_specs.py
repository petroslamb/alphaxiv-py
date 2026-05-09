"""Validate the repo-local feature spec scaffold."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_SECTIONS = (
    "Status",
    "Endpoint Evidence",
    "Acceptance Criteria",
    "Validation Commands",
)
STATUS_PATTERN = re.compile(r"^Status:\s*(?P<status>[A-Za-z][A-Za-z -]*)\s*$", re.MULTILINE)
FEATURE_LINK_PATTERN = re.compile(r"\]\((features/[^)]+\.md)\)")
SECTION_PATTERN = re.compile(r"^## (?P<title>.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class SpecCheckResult:
    path: Path
    message: str


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(path: Path, root: Path, errors: list[SpecCheckResult]) -> str | None:
    if not path.exists():
        errors.append(SpecCheckResult(path, f"{_relative(path, root)} is missing"))
        return None
    return path.read_text(encoding="utf-8")


def _sections(markdown: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[match.group("title").strip()] = markdown[start:end].strip()
    return sections


def _check_feature_spec(path: Path, root: Path) -> list[SpecCheckResult]:
    errors: list[SpecCheckResult] = []
    text = _read_text(path, root, errors)
    if text is None:
        return errors

    rel_path = _relative(path, root)
    if not text.startswith("# "):
        errors.append(SpecCheckResult(path, f"{rel_path} must start with a level-1 heading"))

    sections = _sections(text)
    for required in REQUIRED_SECTIONS:
        body = sections.get(required)
        if body is None:
            errors.append(SpecCheckResult(path, f"{rel_path} is missing ## {required}"))
        elif not body.strip():
            errors.append(SpecCheckResult(path, f"{rel_path} has an empty ## {required} section"))

    status_body = sections.get("Status", "")
    if status_body and not STATUS_PATTERN.search(status_body):
        errors.append(SpecCheckResult(path, f"{rel_path} must include a 'Status: <value>' line"))

    validation_body = sections.get("Validation Commands", "")
    if validation_body and "uv run" not in validation_body:
        errors.append(
            SpecCheckResult(path, f"{rel_path} validation commands must include a uv run command")
        )

    return errors


def _check_index(root: Path, feature_specs: list[Path]) -> list[SpecCheckResult]:
    errors: list[SpecCheckResult] = []
    index_path = root / "specs" / "README.md"
    text = _read_text(index_path, root, errors)
    if text is None:
        return errors

    linked_specs = set(FEATURE_LINK_PATTERN.findall(text))
    expected_specs = {
        path.relative_to(root / "specs").as_posix()
        for path in feature_specs
        if path.name != "README.md"
    }

    for missing in sorted(expected_specs - linked_specs):
        errors.append(SpecCheckResult(index_path, f"specs/README.md does not link {missing}"))
    for stale in sorted(linked_specs - expected_specs):
        errors.append(SpecCheckResult(index_path, f"specs/README.md links missing {stale}"))

    return errors


def check_specs(root: Path) -> list[SpecCheckResult]:
    root = root.resolve()
    errors: list[SpecCheckResult] = []
    specs_dir = root / "specs"
    features_dir = specs_dir / "features"
    template_path = specs_dir / "templates" / "feature-spec-template.md"

    _read_text(specs_dir / "README.md", root, errors)
    _read_text(template_path, root, errors)

    if not features_dir.exists():
        errors.append(SpecCheckResult(features_dir, "specs/features is missing"))
        return errors

    feature_specs = sorted(features_dir.glob("*.md"))
    if not feature_specs:
        errors.append(SpecCheckResult(features_dir, "specs/features has no feature specs"))
        return errors

    errors.extend(_check_index(root, feature_specs))
    for spec_path in feature_specs:
        errors.extend(_check_feature_spec(spec_path, root))

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to validate.",
    )
    args = parser.parse_args(argv)

    errors = check_specs(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error.message}", file=sys.stderr)
        return 1

    print("Spec check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
