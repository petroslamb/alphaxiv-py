"""Shared loading helpers for packaged and repo-level agent assets."""

from __future__ import annotations

import os
import re
from contextlib import suppress
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from . import __version__
from .catalog import INTEGRATION_TARGETS, IntegrationTarget

if TYPE_CHECKING:
    from importlib.abc import Traversable


VERSION_MARKER_RE = re.compile(r"alphaxiv-py v([\d.]+)")
REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = resources.files("alphaxiv")


def get_integration_target(target: str) -> IntegrationTarget:
    """Return metadata for one supported integration target."""
    return INTEGRATION_TARGETS[target]


def get_scope_root(scope: str, *, target: str | None = None) -> Path:
    """Resolve the root directory for a given install scope."""
    if scope == "project":
        return Path.cwd()
    if target == "codex":
        codex_home = os.environ.get("CODEX_HOME")
        if codex_home:
            return Path(codex_home)
    return Path.home()


def get_install_destination(target: str, scope: str) -> Path:
    """Resolve the destination path for one target and scope."""
    metadata = get_integration_target(target)
    relative = metadata.project_relative_path if scope == "project" else metadata.user_relative_path
    base = get_scope_root(scope, target=target)
    if target == "codex" and scope == "user" and os.environ.get("CODEX_HOME"):
        return base / "skills" / "alphaxiv"
    return base / relative


def get_primary_install_path(target: str, scope: str) -> Path:
    """Resolve the primary installed file for a target."""
    metadata = get_integration_target(target)
    destination = get_install_destination(target, scope)
    if metadata.kind == "directory":
        return destination / metadata.primary_relative_path
    return destination


def _repo_source_path(target: str) -> Path:
    return REPO_ROOT / get_integration_target(target).repo_source


def _package_source_path(target: str) -> Traversable:
    return PACKAGE_ROOT.joinpath(*get_integration_target(target).package_source.parts)


def has_repo_source(target: str) -> bool:
    """Return whether the repository source asset exists on disk."""
    return _repo_source_path(target).exists()


def _iter_tree(node: Path | Traversable, prefix: Path = Path(".")) -> list[tuple[Path, str]]:
    items: list[tuple[Path, str]] = []
    if node.is_file():
        items.append((prefix, node.read_text(encoding="utf-8")))
        return items
    for child in sorted(node.iterdir(), key=lambda entry: entry.name):
        child_prefix = prefix / child.name if prefix != Path(".") else Path(child.name)
        if child.is_dir():
            items.extend(_iter_tree(child, child_prefix))
        elif child.is_file():
            items.append((child_prefix, child.read_text(encoding="utf-8")))
    return items


def get_source_bundle(target: str) -> dict[Path, str]:
    """Return the installable source bundle for a target."""
    repo_source = _repo_source_path(target)
    if repo_source.exists():
        if repo_source.is_file():
            return {Path(repo_source.name): repo_source.read_text(encoding="utf-8")}
        return {path: content for path, content in _iter_tree(repo_source)}

    package_source = _package_source_path(target)
    if package_source.is_file():
        return {Path(package_source.name): package_source.read_text(encoding="utf-8")}
    if package_source.is_dir():
        return {path: content for path, content in _iter_tree(package_source)}
    return {}


def get_source_text(target: str) -> str | None:
    """Return the primary source file text for a target."""
    bundle = get_source_bundle(target)
    primary = get_integration_target(target).primary_relative_path
    if get_integration_target(target).kind == "file":
        primary = Path(primary.name)
    return bundle.get(primary)


def render_source_bundle(target: str) -> str | None:
    """Render an install bundle as one text block with file headings."""
    bundle = get_source_bundle(target)
    if not bundle:
        return None

    if len(bundle) == 1:
        return next(iter(bundle.values()))

    parts: list[str] = []
    for relative_path in sorted(bundle):
        parts.append(f"# {relative_path.as_posix()}\n")
        parts.append(bundle[relative_path].rstrip())
        parts.append("\n")
    return "\n".join(parts).rstrip() + "\n"


def add_version_comment(content: str, *, version: str | None = None) -> str:
    """Embed the CLI version into an installed Markdown/YAML-like asset."""
    resolved_version = version or __version__
    marker = f"<!-- alphaxiv-py v{resolved_version} -->\n"
    if content.startswith("---\n") and "\n---\n" in content:
        start = content.find("\n---\n")
        frontmatter = content[: start + 5]
        rest = content[start + 5 :].lstrip()
        return f"{frontmatter}{marker}{rest}"
    if content.startswith("interface:\n") or content.startswith("# "):
        return marker + content
    return marker + content


def add_yaml_version_comment(content: str, *, version: str | None = None) -> str:
    """Embed the CLI version into YAML content."""
    resolved_version = version or __version__
    marker = f"# alphaxiv-py v{resolved_version}\n"
    return marker + content


def stamp_bundle(
    target: str, bundle: dict[Path, str], *, version: str | None = None
) -> dict[Path, str]:
    """Add install-time version markers to bundle files."""
    stamped: dict[Path, str] = {}
    for relative_path, content in bundle.items():
        if relative_path.suffix in {".yaml", ".yml"}:
            stamped[relative_path] = add_yaml_version_comment(content, version=version)
        else:
            stamped[relative_path] = add_version_comment(content, version=version)
    return stamped


def strip_version_markers(content: str) -> str:
    """Remove install-time version comment lines from content."""
    lines = content.splitlines(keepends=True)
    cleaned: list[str] = []
    for index, line in enumerate(lines):
        if index < 6 and (
            line.startswith("<!-- alphaxiv-py v") or line.startswith("# alphaxiv-py v")
        ):
            continue
        cleaned.append(line)
    return "".join(cleaned)


def get_installed_bundle(target: str, scope: str) -> dict[Path, str]:
    """Read the currently installed files for a target and scope."""
    metadata = get_integration_target(target)
    destination = get_install_destination(target, scope)
    if metadata.kind == "file":
        if not destination.exists():
            return {}
        return {Path(destination.name): destination.read_text(encoding="utf-8")}
    if not destination.exists():
        return {}
    return {path: content for path, content in _iter_tree(destination)}


def get_installed_content(target: str, scope: str) -> str | None:
    """Render the installed target bundle or file."""
    bundle = get_installed_bundle(target, scope)
    if not bundle:
        return None
    if len(bundle) == 1:
        return next(iter(bundle.values()))
    parts: list[str] = []
    for relative_path in sorted(bundle):
        parts.append(f"# {relative_path.as_posix()}\n")
        parts.append(bundle[relative_path].rstrip())
        parts.append("\n")
    return "\n".join(parts).rstrip() + "\n"


def get_installed_version(target: str, scope: str) -> str | None:
    """Extract the installed version marker from the primary file."""
    primary = get_primary_install_path(target, scope)
    if not primary.exists():
        return None
    content = primary.read_text(encoding="utf-8")[:500]
    match = VERSION_MARKER_RE.search(content)
    return match.group(1) if match else None


def installed_matches_source(target: str, scope: str) -> bool:
    """Return whether the installed files match the source bundle ignoring version markers."""
    installed = get_installed_bundle(target, scope)
    if not installed:
        return False
    source = get_source_bundle(target)
    if not source:
        return False
    normalized_installed = {
        path: strip_version_markers(content) for path, content in installed.items()
    }
    normalized_source = dict(source)
    return normalized_installed == normalized_source


def write_bundle(target: str, scope: str, bundle: dict[Path, str]) -> Path:
    """Write an install bundle to disk and return the destination root."""
    metadata = get_integration_target(target)
    destination = get_install_destination(target, scope)
    if metadata.kind == "file":
        destination.parent.mkdir(parents=True, exist_ok=True)
        relative = Path(destination.name)
        destination.write_text(bundle[relative], encoding="utf-8")
        return destination

    destination.mkdir(parents=True, exist_ok=True)
    for relative_path, content in bundle.items():
        target_path = destination / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
    return destination


def remove_installed_target(target: str, scope: str) -> bool:
    """Remove one installed target bundle when it is managed by the CLI."""
    metadata = get_integration_target(target)
    destination = get_install_destination(target, scope)
    primary = get_primary_install_path(target, scope)
    if not primary.exists():
        return False
    if get_installed_version(target, scope) is None:
        return False

    if metadata.kind == "file":
        destination.unlink()
        return True

    for path in sorted(destination.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        else:
            with suppress(OSError):
                path.rmdir()
    with suppress(OSError):
        destination.rmdir()
    return True


def remove_empty_parents(path: Path, scope: str, *, target: str | None = None) -> None:
    """Remove empty parent directories without deleting the scope root."""
    stop_at = get_scope_root(scope, target=target)
    current = path.parent if path.is_file() else path
    while current != stop_at:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent
