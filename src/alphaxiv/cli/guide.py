"""Workflow-oriented guide commands."""

from __future__ import annotations

from textwrap import dedent

import click
from rich.table import Table

from ..catalog import GUIDE_ENTRIES, GuideEntry
from .grouped import WrappedHelpGroup
from .helpers import console


@click.group(
    "guide",
    cls=WrappedHelpGroup,
    invoke_without_command=True,
    help=(
        "Show higher-level alphaXiv workflows instead of command reference details.\n\n"
        "Use `guide` when you want to combine `search`, `feed`, `paper`, `assistant`, and "
        "`context` into a research task.\n\n"
        "Examples:\n"
        "  alphaxiv guide research\n"
        "  alphaxiv guide paper\n"
        "  alphaxiv guide assistant\n"
        "  alphaxiv guide feed"
    ),
)
@click.pass_context
def guide(ctx: click.Context) -> None:
    """Show the available workflow guides."""
    if ctx.invoked_subcommand is not None:
        return

    console.print("[bold]alphaXiv Workflow Guides[/bold]")
    console.print("Use these when `--help` is not enough and you need a task-level workflow.")
    console.print()

    table = Table(title="Available Guides")
    table.add_column("Guide")
    table.add_column("What It Covers")
    for name in ("research", "paper", "assistant", "feed"):
        entry = GUIDE_ENTRIES[name]
        table.add_row(name, entry.summary)
    console.print(table)
    console.print()
    console.print("Run `alphaxiv guide <name>` to print the full workflow.")


def _render_guide(entry: GuideEntry) -> None:
    console.print(f"[bold]{entry.title}[/bold]")
    console.print(entry.summary)
    console.print()
    console.print(dedent(entry.body).strip())


@guide.command("research")
def guide_research() -> None:
    """Show the recommended workflow for finding and shortlisting papers."""
    _render_guide(GUIDE_ENTRIES["research"])


@guide.command("paper")
def guide_paper() -> None:
    """Show how to choose between paper inspection commands."""
    _render_guide(GUIDE_ENTRIES["paper"])


@guide.command("assistant")
def guide_assistant() -> None:
    """Show when to use the assistant after deterministic retrieval."""
    _render_guide(GUIDE_ENTRIES["assistant"])


@guide.command("feed")
def guide_feed() -> None:
    """Show how to use feed filters and ranking modes for discovery."""
    _render_guide(GUIDE_ENTRIES["feed"])
