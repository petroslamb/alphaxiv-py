"""Human-readable agent integration guidance."""

from __future__ import annotations

import click
from rich.table import Table

from ..agent_assets import get_install_destination, get_source_bundle
from ..catalog import INTEGRATION_TARGETS
from .grouped import WrappedHelpGroup
from .helpers import console


@click.group(
    "agent",
    cls=WrappedHelpGroup,
    help=(
        "Show target-specific guidance for Codex, Claude Code, and OpenCode integrations.\n\n"
        "Use `agent show <target>` to inspect what gets installed and where it will live on disk."
    ),
)
def agent() -> None:
    """Inspect supported agent integration targets."""


@agent.command("show")
@click.argument("target", type=click.Choice(tuple(INTEGRATION_TARGETS), case_sensitive=False))
def show_agent(target: str) -> None:
    """Show installation paths and included files for one supported target."""
    metadata = INTEGRATION_TARGETS[target]
    console.print(f"[bold]{metadata.label}[/bold]")
    console.print(metadata.description)
    console.print()
    console.print(metadata.guidance)
    console.print()

    table = Table(title=f"{metadata.label} Install Paths")
    table.add_column("Scope")
    table.add_column("Path")
    table.add_row("user", str(get_install_destination(target, "user")))
    table.add_row("project", str(get_install_destination(target, "project")))
    console.print(table)

    bundle = get_source_bundle(target)
    if bundle:
        files = Table(title=f"{metadata.label} Installed Files")
        files.add_column("Path")
        for relative_path in sorted(bundle):
            files.add_row(relative_path.as_posix())
        console.print()
        console.print(files)
