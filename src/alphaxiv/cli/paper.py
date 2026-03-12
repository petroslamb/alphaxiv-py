"""Paper-oriented CLI commands."""

from __future__ import annotations

import click
from rich.table import Table

from ..types import OverviewStatus, Paper, PaperFullText, PaperOverview, PaperResources, PaperTranscript
from .helpers import console, get_effective_identifier, make_client, run_async

paper = click.Group("paper", help="Paper metadata commands.")


def fetch_paper(identifier: str) -> Paper:
    async def _get() -> Paper:
        async with make_client() as client:
            return await client.papers.get(identifier)

    return run_async(_get())


def fetch_overview(identifier: str, language: str = "en") -> PaperOverview:
    async def _get() -> PaperOverview:
        async with make_client() as client:
            return await client.papers.overview(identifier, language=language)

    return run_async(_get())


def fetch_resources(identifier: str) -> PaperResources:
    async def _get() -> PaperResources:
        async with make_client() as client:
            return await client.papers.resources(identifier)

    return run_async(_get())


def fetch_overview_status(identifier: str) -> OverviewStatus:
    async def _get() -> OverviewStatus:
        async with make_client() as client:
            return await client.papers.overview_status(identifier)

    return run_async(_get())


def fetch_transcript(identifier: str) -> PaperTranscript:
    async def _get() -> PaperTranscript:
        async with make_client() as client:
            return await client.papers.transcript(identifier)

    return run_async(_get())


def fetch_bibtex(identifier: str) -> str | None:
    async def _get() -> str | None:
        async with make_client() as client:
            return await client.papers.bibtex(identifier)

    return run_async(_get())


def fetch_full_text(identifier: str) -> PaperFullText:
    async def _get() -> PaperFullText:
        async with make_client() as client:
            return await client.papers.full_text(identifier)

    return run_async(_get())


@paper.command("show")
@click.argument("paper_id", required=False)
def show_paper(paper_id: str | None) -> None:
    """Show paper metadata."""
    identifier = get_effective_identifier(paper_id)
    paper_obj = fetch_paper(identifier)

    table = Table(title=paper_obj.version.title)
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Bare ID", paper_obj.resolved.versionless_id or "-")
    table.add_row("Canonical ID", paper_obj.resolved.canonical_id or "-")
    table.add_row("Version UUID", paper_obj.resolved.version_id or "-")
    table.add_row("Group UUID", paper_obj.resolved.group_id or "-")
    table.add_row("Authors", ", ".join(author.full_name for author in paper_obj.authors) or "-")
    table.add_row("Topics", ", ".join(paper_obj.group.topics) or "-")
    table.add_row("PDF URL", paper_obj.pdf_url or "-")
    table.add_row("Source URL", paper_obj.group.source_url or "-")
    console.print(table)


@paper.command("text")
@click.argument("paper_id", required=False)
@click.option(
    "--page",
    "pages",
    multiple=True,
    type=int,
    help="Print only the selected 1-based page numbers. Repeat to include multiple pages.",
)
def show_text(paper_id: str | None, pages: tuple[int, ...]) -> None:
    """Show the public full text for a paper."""
    identifier = get_effective_identifier(paper_id)
    full_text = fetch_full_text(identifier)

    selected_pages = full_text.pages
    if pages:
        page_map = {page.page_number: page for page in full_text.pages}
        requested_pages = list(dict.fromkeys(pages))
        missing_pages = [page for page in requested_pages if page not in page_map]
        if missing_pages:
            raise click.ClickException(
                f"Requested pages were not available: {', '.join(str(page) for page in missing_pages)}"
            )
        selected_pages = [page_map[page_number] for page_number in requested_pages]

    console.print(
        f"[bold]Full Text[/bold] for {full_text.resolved.preferred_id} "
        f"({full_text.page_count} page{'s' if full_text.page_count != 1 else ''})"
    )
    for index, page in enumerate(selected_pages):
        if index == 0:
            console.print()
        else:
            console.print("\n")
        console.print(f"[bold]Page {page.page_number}[/bold]")
        console.print(page.text or "[dim]No text returned.[/dim]")


def register_paper_commands(cli):
    @cli.command("overview")
    @click.argument("paper_id", required=False)
    @click.option("--language", default="en", show_default=True)
    @click.option("--machine", is_flag=True, help="Print the raw machine-readable overview markdown.")
    def overview(paper_id: str | None, language: str, machine: bool) -> None:
        """Show the AI overview for a paper."""
        identifier = get_effective_identifier(paper_id)
        overview_obj = fetch_overview(identifier, language=language)
        if machine:
            console.print(overview_obj.overview_markdown)
            return
        console.print(f"[bold]{overview_obj.title}[/bold]")
        if overview_obj.summary:
            console.print(f"\n[bold]Summary[/bold]\n{overview_obj.summary.summary}")
        console.print(f"\n[bold]Overview[/bold]\n{overview_obj.overview_markdown}")

    @cli.command("overview-status")
    @click.argument("paper_id", required=False)
    def overview_status(paper_id: str | None) -> None:
        """Show overview generation and translation status for a paper."""
        identifier = get_effective_identifier(paper_id)
        status_obj = fetch_overview_status(identifier)
        table = Table(title="Overview Status")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Version UUID", status_obj.version_id)
        table.add_row("State", status_obj.state or "-")
        table.add_row("Updated At", status_obj.updated_at.isoformat() if status_obj.updated_at else "-")
        table.add_row(
            "Languages",
            ", ".join(sorted(status_obj.translations)) if status_obj.translations else "-",
        )
        console.print(table)

        if status_obj.translations:
            translations = Table(title="Overview Translations")
            translations.add_column("Language")
            translations.add_column("State")
            translations.add_column("Requested At")
            translations.add_column("Updated At")
            translations.add_column("Error")
            for language in sorted(status_obj.translations):
                translation = status_obj.translations[language]
                translations.add_row(
                    language,
                    translation.state or "-",
                    translation.requested_at.isoformat() if translation.requested_at else "-",
                    translation.updated_at.isoformat() if translation.updated_at else "-",
                    translation.error or "-",
                )
            console.print(translations)

    @cli.command("resources")
    @click.argument("paper_id", required=False)
    @click.option("--bibtex", "show_bibtex", is_flag=True, help="Print the paper BibTeX citation.")
    @click.option(
        "--transcript",
        "show_transcript",
        is_flag=True,
        help="Print the AI audio summary transcript when available.",
    )
    def resources(paper_id: str | None, show_bibtex: bool, show_transcript: bool) -> None:
        """Show public resources for a paper."""
        if show_bibtex and show_transcript:
            raise click.ClickException("Use either --bibtex or --transcript, not both.")

        identifier = get_effective_identifier(paper_id)
        if show_bibtex:
            bibtex = fetch_bibtex(identifier)
            if not bibtex:
                raise click.ClickException(f"No BibTeX citation was available for '{identifier}'.")
            console.print(bibtex)
            return

        if show_transcript:
            transcript = fetch_transcript(identifier)
            console.print(
                f"[bold]Audio Transcript[/bold] for {transcript.resolved.preferred_id} "
                f"({len(transcript.lines)} lines)"
            )
            console.print()
            for line in transcript.lines:
                prefix = f"[bold]{line.speaker}:[/bold] " if line.speaker else ""
                console.print(f"{prefix}{line.line}")
            return

        resources_obj = fetch_resources(identifier)
        table = Table(title="Paper Resources")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Canonical ID", resources_obj.resolved.canonical_id or "-")
        table.add_row("PDF URL", resources_obj.pdf_url or "-")
        table.add_row("Source URL", resources_obj.source_url or "-")
        table.add_row("BibTeX", "available" if resources_obj.citation else "-")
        table.add_row("Podcast Path", resources_obj.podcast_path or "-")
        table.add_row("Podcast URL", resources_obj.podcast_url or "-")
        table.add_row("Transcript URL", resources_obj.transcript_url or "-")
        table.add_row("Mentions", str(len(resources_obj.mentions)))
        table.add_row(
            "Implementations",
            ", ".join(item.url for item in resources_obj.implementations) or "-",
        )
        console.print(table)
