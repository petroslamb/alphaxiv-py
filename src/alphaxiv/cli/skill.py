"""Skill and agent integration management commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click

from .. import __version__
from ..agent_assets import (
    get_install_destination,
    get_installed_version,
    get_integration_target,
    get_primary_install_path,
    get_source_bundle,
    get_source_text,
    installed_matches_source,
    remove_empty_parents,
    remove_installed_target,
    render_source_bundle,
    stamp_bundle,
    write_bundle,
)
from ..catalog import INTEGRATION_TARGETS
from .grouped import WrappedHelpGroup
from .helpers import console, print_json
from .messages import click_error

SCOPES = ("user", "project")
STATUS_SCOPES = ("user", "project", "all")
TARGET_NAMES = tuple(INTEGRATION_TARGETS)


@dataclass(frozen=True, slots=True)
class SkillStatusRecord:
    target: str
    label: str
    scope: str
    path: str
    installed: bool
    managed: bool
    source_copy: bool
    version: str | None
    expected_version: str
    needs_update: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "label": self.label,
            "scope": self.scope,
            "path": self.path,
            "installed": self.installed,
            "managed": self.managed,
            "source_copy": self.source_copy,
            "version": self.version,
            "expected_version": self.expected_version,
            "needs_update": self.needs_update,
        }


@click.group(
    "skill",
    cls=WrappedHelpGroup,
    help=(
        "Install and inspect alphaXiv agent integrations for Codex, Claude Code, and OpenCode.\n\n"
        "Use `skill install` to copy the packaged assets into a supported agent directory, "
        "`skill status` to inspect installed targets, and `skill show` to print the bundled "
        "source content.\n\n"
        "Examples:\n"
        "  alphaxiv skill install\n"
        "  alphaxiv skill status --scope all\n"
        "  alphaxiv skill show --target codex\n"
        "  alphaxiv skill uninstall --target opencode --yes"
    ),
)
def skill() -> None:
    """Manage supported alphaXiv agent integrations."""


def _iter_targets(target_name: str) -> list[str]:
    return list(TARGET_NAMES) if target_name == "all" else [target_name]


def _iter_scopes(scope: str) -> list[str]:
    return list(SCOPES) if scope == "all" else [scope]


def _status_record(target: str, scope: str) -> SkillStatusRecord:
    metadata = get_integration_target(target)
    primary_path = get_primary_install_path(target, scope)
    installed = primary_path.exists()
    version = get_installed_version(target, scope)
    source_copy = installed and version is None and installed_matches_source(target, scope)
    managed = version is not None
    return SkillStatusRecord(
        target=target,
        label=metadata.label,
        scope=scope,
        path=str(get_install_destination(target, scope)),
        installed=installed,
        managed=managed,
        source_copy=source_copy,
        version=version,
        expected_version=__version__,
        needs_update=managed and version != __version__,
    )


def _human_status_label(record: SkillStatusRecord) -> str:
    if not record.installed:
        return "[yellow]Not installed[/yellow]"
    if record.source_copy and not record.managed:
        return "[cyan]Source copy detected[/cyan]"
    return "[green]Installed[/green]"


@skill.command("install")
@click.option(
    "--target",
    "target_name",
    type=click.Choice(["all", *TARGET_NAMES], case_sensitive=False),
    default="all",
    show_default=True,
    help="Install the Codex skill, Claude Code subagent, OpenCode command pack, or all of them.",
)
@click.option(
    "--scope",
    type=click.Choice(SCOPES, case_sensitive=False),
    default="user",
    show_default=True,
    help="Install for the current user or into the current project.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite an existing unmanaged target instead of refusing to touch it.",
)
def install_skill(target_name: str, scope: str, force: bool) -> None:
    """Install or update the packaged agent integrations."""
    installed: list[tuple[str, Path]] = []
    skipped: list[str] = []
    failures: list[str] = []

    for target in _iter_targets(target_name):
        bundle = get_source_bundle(target)
        if not bundle:
            failures.append(
                f"{get_integration_target(target).label}: source assets were not found."
            )
            continue

        record = _status_record(target, scope)
        if record.installed and not record.managed and not force:
            if record.source_copy:
                skipped.append(f"{record.label}: already available as a source checkout copy.")
            else:
                failures.append(
                    f"{record.label}: {record.path} already exists and is not managed by alphaxiv. "
                    "Re-run with --force to overwrite it."
                )
            continue

        stamped_bundle = stamp_bundle(target, bundle)
        destination = write_bundle(target, scope, stamped_bundle)
        installed.append((target, destination))

    if installed:
        console.print("[green]Installed[/green] alphaXiv agent integrations")
        console.print(f"  Version: {__version__}")
        console.print(f"  Scope:   {scope}")
        for target, destination in installed:
            console.print(f"  {get_integration_target(target).label}: {destination}")

    for message in skipped:
        console.print(f"[cyan]Skipped[/cyan] {message}")

    for message in failures:
        console.print(f"[red]Failed[/red] {message}")

    if failures:
        raise SystemExit(1)


@skill.command("status")
@click.option(
    "--scope",
    type=click.Choice(STATUS_SCOPES, case_sensitive=False),
    default="user",
    show_default=True,
    help="Inspect user-level installs, project-level installs, or both.",
)
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def skill_status(scope: str, json_output: bool) -> None:
    """Show installed integration status and version information."""
    records = [
        _status_record(target, item_scope)
        for item_scope in _iter_scopes(scope)
        for target in TARGET_NAMES
    ]
    if json_output:
        print_json(
            {
                "cli_version": __version__,
                "records": [record.to_dict() for record in records],
            }
        )
        return

    console.print(f"[bold]alphaXiv integration status[/bold] ({scope} scope)")
    console.print(f"CLI version: {__version__}")
    for item_scope in _iter_scopes(scope):
        console.print()
        console.print(f"[bold]{item_scope.title()} scope[/bold]")
        for record in [record for record in records if record.scope == item_scope]:
            console.print(f"  {record.label}: {_human_status_label(record)}")
            console.print(f"    Path: {record.path}")
            if record.installed and record.managed:
                console.print(f"    Installed version: {record.version or 'unknown'}")
                if record.needs_update:
                    console.print(
                        "    [yellow]Version mismatch[/yellow] - run `alphaxiv skill install`"
                    )
            elif record.source_copy:
                console.print("    Managed by: repository/source checkout")


@skill.command("show")
@click.option(
    "--target",
    "target_name",
    type=click.Choice(["source", *TARGET_NAMES], case_sensitive=False),
    default="source",
    show_default=True,
    help="Show the canonical Codex skill source or one target-specific packaged bundle.",
)
def show_skill(target_name: str) -> None:
    """Display the bundled source content for one integration target."""
    if target_name == "source":
        content = get_source_text("codex")
        if content is None:
            raise click_error("The packaged Codex skill source was not found.")
        console.print(content)
        return

    content = render_source_bundle(target_name)
    if content is None:
        raise click_error(
            f"The packaged {get_integration_target(target_name).label} assets were not found."
        )
    console.print(content)


@skill.command("uninstall")
@click.option(
    "--target",
    "target_name",
    type=click.Choice(["all", *TARGET_NAMES], case_sensitive=False),
    default="all",
    show_default=True,
    help="Remove the Codex skill, Claude Code subagent, OpenCode command pack, or all of them.",
)
@click.option(
    "--scope",
    type=click.Choice(SCOPES, case_sensitive=False),
    default="user",
    show_default=True,
    help="Remove integrations from the current user or the current project.",
)
@click.option("--yes", is_flag=True, help="Remove the selected targets without prompting.")
def uninstall_skill(target_name: str, scope: str, yes: bool) -> None:
    """Remove managed integration files from disk."""
    if not yes:
        click.confirm(
            f"Remove alphaXiv integrations for {target_name} from {scope} scope?",
            abort=True,
        )

    removed: list[str] = []
    skipped: list[str] = []
    for target in _iter_targets(target_name):
        record = _status_record(target, scope)
        if not record.installed:
            continue
        if not record.managed:
            skipped.append(f"{record.label}: refusing to remove unmanaged files at {record.path}.")
            continue
        destination = get_install_destination(target, scope)
        if remove_installed_target(target, scope):
            remove_empty_parents(destination, scope, target=target)
            removed.append(target)

    if removed:
        console.print("[green]Removed[/green] alphaXiv integrations")
        for target in removed:
            console.print(f"  {get_integration_target(target).label}")
    if skipped:
        for message in skipped:
            console.print(f"[yellow]Skipped[/yellow] {message}")
    if not removed and not skipped:
        console.print("[yellow]No managed alphaXiv integrations were installed.[/yellow]")
