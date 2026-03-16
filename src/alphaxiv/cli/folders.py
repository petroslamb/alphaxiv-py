"""Authenticated folder CLI commands."""

from __future__ import annotations

import click
from rich.table import Table

from ..types import Folder
from .grouped import WrappedHelpGroup
from .helpers import console, make_client, print_json, run_async_with_click_errors
from .serialize import reject_raw_and_json, serialize_folder

folders = WrappedHelpGroup(
    "folders",
    help=(
        "Inspect authenticated alphaXiv folders and the papers saved inside them.\n\n"
        "Examples:\n"
        "  alphaxiv folders list\n"
        "  alphaxiv folders list --papers\n"
        '  alphaxiv folders show "Want to read"'
    ),
)


def fetch_folders() -> list[Folder]:
    async def _list() -> list[Folder]:
        async with make_client() as client:
            return await client.folders.list()

    return run_async_with_click_errors(_list(), see_help="alphaxiv folders --help")


def fetch_folder(selector: str) -> Folder:
    async def _get() -> Folder:
        async with make_client() as client:
            return await client.folders.get(selector)

    return run_async_with_click_errors(
        _get(),
        suggestions=(
            "alphaxiv folders list",
            'alphaxiv folders show "Want to read"',
        ),
        see_help="alphaxiv folders --help",
    )


def _render_folder_papers(folder: Folder) -> None:
    papers_table = Table(title=f"{folder.name} Papers")
    papers_table.add_column("Paper ID")
    papers_table.add_column("Title")
    papers_table.add_column("Authors")
    papers_table.add_column("Added")
    papers_table.add_column("Topics")
    for paper in folder.papers:
        papers_table.add_row(
            paper.preferred_id,
            paper.title or "-",
            ", ".join(paper.authors[:3]) or "-",
            paper.added_at.date().isoformat() if paper.added_at else "-",
            ", ".join(paper.topics[:3]) or "-",
        )
    console.print(papers_table)


@folders.command("list")
@click.option(
    "--papers",
    "show_papers",
    is_flag=True,
    help="Also print the papers contained in each returned folder.",
)
@click.option("--raw", is_flag=True, help="Print the raw folders JSON payload.")
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def list_folders(show_papers: bool, raw: bool, json_output: bool) -> None:
    """List your alphaXiv folders, optionally including the papers inside them."""
    reject_raw_and_json(raw, json_output, see_help="alphaxiv folders list --help")
    folder_items = fetch_folders()
    if raw:
        print_json([folder.raw for folder in folder_items])
        return
    if json_output:
        print_json(
            {
                "include_papers": show_papers,
                "folders": [
                    serialize_folder(folder, include_papers=show_papers) for folder in folder_items
                ],
            }
        )
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
        _render_folder_papers(folder)


@folders.command("show")
@click.argument("folder")
@click.option("--raw", is_flag=True, help="Print the raw folder JSON payload.")
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def show_folder(folder: str, raw: bool, json_output: bool) -> None:
    """Show one folder and the full paper list currently saved inside it."""
    reject_raw_and_json(raw, json_output, see_help="alphaxiv folders show --help")
    folder_item = fetch_folder(folder)
    if raw:
        print_json(folder_item.raw)
        return
    if json_output:
        print_json(serialize_folder(folder_item, include_papers=True))
        return

    table = Table(title=folder_item.name)
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Folder ID", folder_item.id)
    table.add_row("Type", folder_item.folder_type or "-")
    table.add_row("Sharing", folder_item.sharing_status or "-")
    table.add_row("Papers", str(folder_item.paper_count))
    console.print(table)
    console.print()
    _render_folder_papers(folder_item)
