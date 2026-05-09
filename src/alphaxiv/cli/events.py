"""Public alphaXiv events CLI commands."""

from __future__ import annotations

import click
from rich.table import Table

from ..types import Event
from .grouped import WrappedHelpGroup
from .helpers import console, make_client, print_json, run_async
from .serialize import serialize_event

events = WrappedHelpGroup(
    "events",
    help=(
        "List public alphaXiv events.\n\n"
        "Examples:\n"
        "  alphaxiv events list\n"
        "  alphaxiv events list --json"
    ),
)


def fetch_events() -> list[Event]:
    async def _events() -> list[Event]:
        async with make_client() as client:
            return await client.events.list()

    return run_async(_events())


def _render_events_table(events_list: list[Event]) -> None:
    table = Table(title="alphaXiv Events")
    table.add_column("Date")
    table.add_column("Title")
    table.add_column("Speaker")
    table.add_column("Organization")
    table.add_column("Link")
    for event in events_list:
        table.add_row(
            event.date or "-",
            event.title,
            event.speaker or "-",
            event.organization or "-",
            event.link or "-",
        )
    console.print(table)


@events.command("list")
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def list_events(json_output: bool) -> None:
    """List public alphaXiv events."""
    events_list = fetch_events()
    if json_output:
        print_json({"events": [serialize_event(event) for event in events_list]})
        return
    _render_events_table(events_list)
