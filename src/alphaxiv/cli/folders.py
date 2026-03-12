"""Authenticated folder CLI commands."""

from __future__ import annotations

import click
from rich.table import Table

from ..types import Folder
from .grouped import WrappedHelpGroup
from .helpers import console, make_client, print_json, run_async

folders = WrappedHelpGroup(
    "folders",
    help="Inspect authenticated alphaXiv folders and the papers saved inside them.",
)


def fetch_folders() -> list[Folder]:
    async def _list() -> list[Folder]:
        async with make_client() as client:
            return await client.folders.list()

    return run_async(_list())


@folders.command("list")
@click.option(
    "--papers",
    "show_papers",
    is_flag=True,
    help="Also print the papers contained in each returned folder.",
)
@click.option("--raw", is_flag=True, help="Print the raw folders JSON payload.")
def list_folders(show_papers: bool, raw: bool) -> None:
    """List the folders available to the authenticated alphaXiv user."""
    folder_items = fetch_folders()
    if raw:
        print_json([folder.raw for folder in folder_items])
        return

    table = Table(title="alphaXiv Folders")
    table.add_column("Folder")
    table.add_column("Type")
    table.add_column("Sharing")
    table.add_column("Papers")
    for folder in folder_items:
        table.add_row(
            folder.name,
            folder.folder_type or "-",
            folder.sharing_status or "-",
            str(folder.paper_count),
        )
    console.print(table)

    if not show_papers:
        return

    for folder in folder_items:
        console.print()
        papers_table = Table(title=f"{folder.name} Papers")
        papers_table.add_column("Paper ID")
        papers_table.add_column("Title")
        papers_table.add_column("Topics")
        for paper in folder.papers:
            papers_table.add_row(
                paper.preferred_id,
                paper.title or "-",
                ", ".join(paper.topics[:3]) or "-",
            )
        console.print(papers_table)
