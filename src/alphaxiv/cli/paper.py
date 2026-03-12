"""Paper-oriented CLI commands."""

from __future__ import annotations

from pathlib import Path

import click
from rich.table import Table
from rich.tree import Tree

from .._comments import VALID_COMMENT_TAGS
from ..exceptions import ResolutionError
from ..types import (
    FeedCard,
    Folder,
    OverviewStatus,
    Paper,
    PaperComment,
    PaperFullText,
    PaperOverview,
    PaperResources,
    PaperTranscript,
)
from .grouped import WrappedHelpGroup
from .helpers import console, get_effective_identifier, make_client, print_json, run_async

paper = WrappedHelpGroup(
    "paper",
    help=(
        "Inspect paper metadata, overviews, resources, comments, PDFs, and paper actions.\n\n"
        "Examples:\n"
        "  alphaxiv paper show 1706.03762\n"
        "  alphaxiv paper overview 1706.03762 --language en\n"
        "  alphaxiv paper comments list 1706.03762\n"
        "  alphaxiv paper pdf download 1706.03762 ./paper.pdf"
    ),
)

paper_comments = WrappedHelpGroup(
    "comments",
    help=(
        "List public paper comments and run authenticated comment mutations.\n\n"
        "Examples:\n"
        "  alphaxiv paper comments list 1706.03762\n"
        '  alphaxiv paper comments add 1706.03762 --body "Helpful overview" --tag general\n'
        '  alphaxiv paper comments reply 1706.03762 comment-root --body "Thanks"'
    ),
)

paper_pdf = WrappedHelpGroup(
    "pdf",
    help="Resolve or download the public PDF for a paper.",
)

paper_folders = WrappedHelpGroup(
    "folders",
    help=(
        "Inspect or mutate the authenticated folder membership for a paper.\n\n"
        "Examples:\n"
        "  alphaxiv paper folders list 1706.03762\n"
        '  alphaxiv paper folders add 1706.03762 "Want to read"\n'
        '  alphaxiv paper folders remove 1706.03762 "Want to read"'
    ),
)


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


def fetch_comments(identifier: str) -> list[PaperComment]:
    async def _get() -> list[PaperComment]:
        async with make_client() as client:
            return await client.papers.comments(identifier)

    return run_async(_get())


def fetch_similar(identifier: str, limit: int | None = None) -> list[FeedCard]:
    async def _get() -> list[FeedCard]:
        async with make_client() as client:
            return await client.papers.similar(identifier, limit=limit)

    return run_async(_get())


def create_comment(
    identifier: str,
    *,
    body: str,
    title: str | None = None,
    tag: str = "general",
) -> PaperComment:
    async def _create() -> PaperComment:
        async with make_client() as client:
            return await client.papers.create_comment(
                identifier,
                body=body,
                title=title,
                tag=tag,
            )

    return run_async(_create())


def reply_to_comment(
    identifier: str,
    comment_id: str,
    *,
    body: str,
    title: str | None = None,
    tag: str = "general",
) -> PaperComment:
    async def _reply() -> PaperComment:
        async with make_client() as client:
            return await client.papers.reply_to_comment(
                identifier,
                comment_id,
                body=body,
                title=title,
                tag=tag,
            )

    return run_async(_reply())


def toggle_comment_upvote(comment_id: str) -> dict[str, object] | None:
    async def _toggle() -> dict[str, object] | None:
        async with make_client() as client:
            return await client.comments.toggle_upvote(comment_id)

    return run_async(_toggle())


def delete_comment(comment_id: str) -> None:
    async def _delete() -> None:
        async with make_client() as client:
            await client.comments.delete(comment_id)

    run_async(_delete())


def toggle_vote(identifier: str) -> dict[str, object] | None:
    async def _toggle() -> dict[str, object] | None:
        async with make_client() as client:
            return await client.papers.toggle_vote(identifier)

    return run_async(_toggle())


def record_view(identifier: str) -> dict[str, object] | None:
    async def _record() -> dict[str, object] | None:
        async with make_client() as client:
            return await client.papers.record_view(identifier)

    return run_async(_record())


def fetch_pdf_url(identifier: str) -> str:
    async def _get() -> str:
        async with make_client() as client:
            return await client.papers.pdf_url(identifier)

    return run_async(_get())


def fetch_pdf_download(identifier: str, path: str | Path) -> Path:
    async def _download() -> Path:
        async with make_client() as client:
            return await client.papers.download_pdf(identifier, path)

    return run_async(_download())


def fetch_paper_folder_membership(identifier: str) -> tuple[str, str, list[Folder]]:
    async def _get() -> tuple[str, str, list[Folder]]:
        async with make_client() as client:
            resolved = await client.papers.resolve(identifier)
            if not resolved.group_id:
                raise ResolutionError(
                    "Paper folder membership requires a bare or versioned arXiv ID. "
                    f"Could not determine a paper group ID for '{identifier}'."
                )
            folders = await client.folders.list()
            return resolved.preferred_id, resolved.group_id, folders

    return run_async(_get())


def add_paper_to_folder(identifier: str, folder_selector: str) -> Folder:
    async def _add() -> Folder:
        async with make_client() as client:
            resolved = await client.papers.resolve(identifier)
            if not resolved.group_id:
                raise ResolutionError(
                    "Paper folder mutations require a bare or versioned arXiv ID. "
                    f"Could not determine a paper group ID for '{identifier}'."
                )
            return await client.folders.add_papers(folder_selector, [resolved.group_id])

    return run_async(_add())


def remove_paper_from_folder(identifier: str, folder_selector: str) -> Folder:
    async def _remove() -> Folder:
        async with make_client() as client:
            resolved = await client.papers.resolve(identifier)
            if not resolved.group_id:
                raise ResolutionError(
                    "Paper folder mutations require a bare or versioned arXiv ID. "
                    f"Could not determine a paper group ID for '{identifier}'."
                )
            return await client.folders.remove_papers(folder_selector, [resolved.group_id])

    return run_async(_remove())


def _confirm_mutation(yes: bool, prompt: str) -> None:
    if yes:
        return
    click.confirm(prompt, abort=True)


def _render_comment(tree: Tree, comment: PaperComment) -> None:
    author = comment.author.display_name if comment.author else "Unknown"
    header_parts = [author]
    if comment.tag:
        header_parts.append(comment.tag)
    header_parts.append(f"{comment.upvotes} upvotes")
    if comment.date:
        header_parts.append(comment.date.isoformat())
    node = tree.add(" | ".join(header_parts))
    if comment.title:
        node.add(f"[bold]{comment.title}[/bold]")
    if comment.body:
        node.add(comment.body)
    for response in comment.responses:
        _render_comment(node, response)


def _render_similar_cards(cards: list[FeedCard]) -> None:
    table = Table(title="Similar Papers")
    table.add_column("Paper ID")
    table.add_column("Title")
    table.add_column("Upvotes")
    table.add_column("Visits")
    table.add_column("Topics")
    for card in cards:
        table.add_row(
            card.paper_id,
            card.title,
            str(card.upvotes),
            str(card.visits),
            ", ".join(card.topics[:3]) or "-",
        )
    console.print(table)


def _render_paper_folder_membership(
    preferred_id: str,
    paper_group_id: str,
    folder_items: list[Folder],
) -> None:
    table = Table(title=f"Folder Membership for {preferred_id}")
    table.add_column("Saved")
    table.add_column("Folder")
    table.add_column("Folder ID")
    table.add_column("Type")
    table.add_column("Papers")
    for folder in folder_items:
        table.add_row(
            "yes" if folder.contains_paper_group_id(paper_group_id) else "no",
            folder.name,
            folder.id,
            folder.folder_type or "-",
            str(folder.paper_count),
        )
    console.print(table)


def _render_summary_sections(overview_obj: PaperOverview) -> None:
    summary = overview_obj.summary
    if summary is None:
        raise click.ClickException(
            f"No structured overview summary was available for '{overview_obj.title}'."
        )

    console.print(f"[bold]{overview_obj.title}[/bold]")
    console.print()
    console.print(summary.summary or "[dim]No summary text returned.[/dim]")

    section_map = [
        ("Original Problem", summary.original_problem),
        ("Solution", summary.solution),
        ("Key Insights", summary.key_insights),
        ("Results", summary.results),
    ]
    for label, items in section_map:
        if not items:
            continue
        console.print()
        console.print(f"[bold]{label}[/bold]")
        for item in items:
            console.print(f"- {item}")


@paper.command("show")
@click.argument("paper_id", required=False)
def show_paper(paper_id: str | None) -> None:
    """Show resolved identifiers and core metadata for a paper."""
    identifier = get_effective_identifier(paper_id)
    paper_obj = fetch_paper(identifier)

    table = Table(title=paper_obj.version.title)
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("arXiv ID", paper_obj.resolved.versionless_id or "-")
    table.add_row("Versioned ID", paper_obj.resolved.canonical_id or "-")
    table.add_row("Version UUID", paper_obj.resolved.version_id or "-")
    table.add_row("Group UUID", paper_obj.resolved.group_id or "-")
    table.add_row("Authors", ", ".join(author.full_name for author in paper_obj.authors) or "-")
    table.add_row("Topics", ", ".join(paper_obj.group.topics) or "-")
    table.add_row("PDF URL", paper_obj.pdf_url or "-")
    table.add_row("Source URL", paper_obj.group.source_url or "-")
    console.print(table)


@paper.command("abstract")
@click.argument("paper_id", required=False)
def show_abstract(paper_id: str | None) -> None:
    """Print the paper title and abstract from the main metadata payload."""
    identifier = get_effective_identifier(paper_id)
    paper_obj = fetch_paper(identifier)
    console.print(f"[bold]{paper_obj.version.title}[/bold]")
    console.print()
    console.print(paper_obj.version.abstract or "[dim]No abstract returned.[/dim]")


@paper.command("summary")
@click.argument("paper_id", required=False)
@click.option("--language", default="en", show_default=True, help="Overview language to request.")
@click.option("--raw", is_flag=True, help="Print the raw structured summary JSON payload.")
def show_summary(paper_id: str | None, language: str, raw: bool) -> None:
    """Print the structured AI summary derived from the overview endpoint."""
    identifier = get_effective_identifier(paper_id)
    overview_obj = fetch_overview(identifier, language=language)
    if raw:
        print_json(overview_obj.summary.raw if overview_obj.summary else {})
        return
    _render_summary_sections(overview_obj)


@paper.command("overview")
@click.argument("paper_id", required=False)
@click.option("--language", default="en", show_default=True, help="Overview language to request.")
@click.option("--machine", is_flag=True, help="Print the raw machine-readable overview markdown.")
def paper_overview(paper_id: str | None, language: str, machine: bool) -> None:
    """Show the generated paper overview in the selected language."""
    identifier = get_effective_identifier(paper_id)
    overview_obj = fetch_overview(identifier, language=language)
    if machine:
        console.print(overview_obj.overview_markdown)
        return
    console.print(f"[bold]{overview_obj.title}[/bold]")
    if overview_obj.summary:
        console.print(f"\n[bold]Summary[/bold]\n{overview_obj.summary.summary}")
    console.print(f"\n[bold]Overview[/bold]\n{overview_obj.overview_markdown}")


@paper.command("overview-status")
@click.argument("paper_id", required=False)
def paper_overview_status(paper_id: str | None) -> None:
    """Show overview generation state and available translation statuses."""
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


@paper.command("resources")
@click.argument("paper_id", required=False)
@click.option("--bibtex", "show_bibtex", is_flag=True, help="Print the paper BibTeX citation.")
@click.option(
    "--transcript",
    "show_transcript",
    is_flag=True,
    help="Print the AI audio summary transcript when available.",
)
def paper_resources(paper_id: str | None, show_bibtex: bool, show_transcript: bool) -> None:
    """Show public paper resources, or print BibTeX or transcript directly."""
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
    table.add_row("Versioned ID", resources_obj.resolved.canonical_id or "-")
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
    """Print extracted paper text, optionally limited to specific page numbers."""
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


@paper_folders.command("list")
@click.argument("paper_id", required=False)
@click.option("--raw", is_flag=True, help="Print the raw folder payloads with membership context.")
def list_paper_folders(paper_id: str | None, raw: bool) -> None:
    """Show which folders currently contain the selected paper."""
    identifier = get_effective_identifier(paper_id)
    preferred_id, paper_group_id, folder_items = fetch_paper_folder_membership(identifier)
    if raw:
        print_json(
            {
                "paper_id": preferred_id,
                "paper_group_id": paper_group_id,
                "folders": [
                    {
                        **folder.raw,
                        "containsPaper": folder.contains_paper_group_id(paper_group_id),
                    }
                    for folder in folder_items
                ],
            }
        )
        return
    _render_paper_folder_membership(preferred_id, paper_group_id, folder_items)


@paper_folders.command("add")
@click.argument("args", nargs=-1)
@click.option("--yes", is_flag=True, help="Apply the mutation without a confirmation prompt.")
def add_paper_folder(args: tuple[str, ...], yes: bool) -> None:
    """Save a paper into one of the authenticated user's folders."""
    if len(args) == 1:
        paper_id = None
        folder_selector = args[0]
    elif len(args) == 2:
        paper_id, folder_selector = args
    else:
        raise click.UsageError("Expected either <folder> or <paper-id> <folder>.")

    identifier = get_effective_identifier(paper_id)
    _confirm_mutation(yes, f"Save '{identifier}' into alphaXiv folder '{folder_selector}'?")
    folder = add_paper_to_folder(identifier, folder_selector)
    console.print(f"[green]Saved[/green] {identifier} [green]to folder[/green] {folder.name}")


@paper_folders.command("remove")
@click.argument("args", nargs=-1)
@click.option("--yes", is_flag=True, help="Apply the mutation without a confirmation prompt.")
def remove_paper_folder(args: tuple[str, ...], yes: bool) -> None:
    """Remove a paper from one of the authenticated user's folders."""
    if len(args) == 1:
        paper_id = None
        folder_selector = args[0]
    elif len(args) == 2:
        paper_id, folder_selector = args
    else:
        raise click.UsageError("Expected either <folder> or <paper-id> <folder>.")

    identifier = get_effective_identifier(paper_id)
    _confirm_mutation(
        yes,
        f"Remove '{identifier}' from alphaXiv folder '{folder_selector}'?",
    )
    folder = remove_paper_from_folder(identifier, folder_selector)
    console.print(f"[green]Removed[/green] {identifier} [green]from folder[/green] {folder.name}")


@paper_comments.command("list")
@click.argument("paper_id", required=False)
@click.option("--raw", is_flag=True, help="Print the raw comments JSON payload.")
def list_comments(paper_id: str | None, raw: bool) -> None:
    """Show the public paper comment thread, including nested replies."""
    identifier = get_effective_identifier(paper_id)
    comments = fetch_comments(identifier)
    if raw:
        print_json([comment.raw for comment in comments])
        return
    if not comments:
        console.print(f"[yellow]No comments were available for '{identifier}'.[/yellow]")
        return
    tree = Tree(f"Comments for {identifier}")
    for comment in comments:
        _render_comment(tree, comment)
    console.print(tree)


@paper_comments.command("add")
@click.argument("paper_id", required=False)
@click.option("--body", required=True, help="Comment body text.")
@click.option("--title", help="Optional comment title shown above the body.")
@click.option(
    "--tag",
    default="general",
    show_default=True,
    type=click.Choice(VALID_COMMENT_TAGS, case_sensitive=False),
    help="Comment tag to attach to the new top-level comment.",
)
def add_comment(paper_id: str | None, body: str, title: str | None, tag: str) -> None:
    """Create a top-level authenticated comment for a paper."""
    identifier = get_effective_identifier(paper_id)
    comment = create_comment(identifier, body=body, title=title, tag=tag)
    console.print(f"[green]Created comment[/green] {comment.id} [green]for[/green] {identifier}")


@paper_comments.command("reply")
@click.argument("args", nargs=-1)
@click.option("--body", required=True, help="Reply body text.")
@click.option("--title", help="Optional reply title shown above the body.")
@click.option(
    "--tag",
    default="general",
    show_default=True,
    type=click.Choice(VALID_COMMENT_TAGS, case_sensitive=False),
    help="Comment tag to attach to the new reply.",
)
def reply_comment(args: tuple[str, ...], body: str, title: str | None, tag: str) -> None:
    """Reply to a comment by id, using paper context or an explicit paper id."""
    if len(args) == 1:
        paper_id = None
        comment_id = args[0]
    elif len(args) == 2:
        paper_id, comment_id = args
    else:
        raise click.UsageError("Expected either <comment-id> or <paper-id> <comment-id>.")

    identifier = get_effective_identifier(paper_id)
    comment = reply_to_comment(
        identifier,
        comment_id,
        body=body,
        title=title,
        tag=tag,
    )
    console.print(f"[green]Created reply[/green] {comment.id} [green]for[/green] {comment_id}")


@paper_comments.command("upvote")
@click.argument("comment_id")
@click.option("--yes", is_flag=True, help="Apply the mutation without a confirmation prompt.")
def upvote_comment(comment_id: str, yes: bool) -> None:
    """Toggle the authenticated upvote state for a single comment id."""
    _confirm_mutation(yes, f"Toggle the alphaXiv upvote state for comment '{comment_id}'?")
    toggle_comment_upvote(comment_id)
    console.print(f"[green]Toggled comment upvote for[/green] {comment_id}")


@paper_comments.command("delete")
@click.argument("comment_id")
@click.option("--yes", is_flag=True, help="Apply the mutation without a confirmation prompt.")
def remove_comment(comment_id: str, yes: bool) -> None:
    """Delete a single authenticated comment by id."""
    _confirm_mutation(yes, f"Delete the alphaXiv comment '{comment_id}'?")
    delete_comment(comment_id)
    console.print(f"[green]Deleted comment[/green] {comment_id}")


@paper.command("similar")
@click.argument("paper_id", required=False)
@click.option(
    "--limit",
    type=click.IntRange(1),
    default=None,
    help="Maximum number of deduplicated similar papers to print.",
)
@click.option("--raw", is_flag=True, help="Print the raw similar-papers JSON payload.")
def show_similar(paper_id: str | None, limit: int | None, raw: bool) -> None:
    """Show papers returned by alphaXiv's similar-papers recommendation endpoint."""
    identifier = get_effective_identifier(paper_id)
    cards = fetch_similar(identifier, limit=limit)
    if raw:
        print_json([card.raw for card in cards])
        return
    if not cards:
        console.print(f"[yellow]No similar papers were returned for '{identifier}'.[/yellow]")
        return
    _render_similar_cards(cards)


@paper.command("vote")
@click.argument("paper_id", required=False)
@click.option("--yes", is_flag=True, help="Apply the mutation without a confirmation prompt.")
def vote_for_paper(paper_id: str | None, yes: bool) -> None:
    """Toggle the authenticated vote state for a paper's group id."""
    identifier = get_effective_identifier(paper_id)
    _confirm_mutation(yes, f"Toggle the alphaXiv vote state for '{identifier}'?")
    toggle_vote(identifier)
    console.print(f"[green]Toggled vote for[/green] {identifier}")


@paper.command("view")
@click.argument("paper_id", required=False)
@click.option("--yes", is_flag=True, help="Apply the mutation without a confirmation prompt.")
def mark_paper_viewed(paper_id: str | None, yes: bool) -> None:
    """Record an authenticated paper-view event for analytics or history."""
    identifier = get_effective_identifier(paper_id)
    _confirm_mutation(yes, f"Record a paper view for '{identifier}'?")
    record_view(identifier)
    console.print(f"[green]Recorded paper view for[/green] {identifier}")


@paper_pdf.command("url")
@click.argument("paper_id", required=False)
def show_pdf_url(paper_id: str | None) -> None:
    """Print the resolved fetcher URL for a paper's public PDF."""
    identifier = get_effective_identifier(paper_id)
    console.print(fetch_pdf_url(identifier))


@paper_pdf.command("download")
@click.argument("args", nargs=-1)
def download_pdf(args: tuple[str, ...]) -> None:
    """Download the paper PDF using the current paper context or an explicit paper id."""
    if len(args) == 1:
        paper_id = None
        path = Path(args[0])
    elif len(args) == 2:
        paper_id = args[0]
        path = Path(args[1])
    else:
        raise click.UsageError("Expected either <path> or <paper-id> <path>.")

    identifier = get_effective_identifier(paper_id)
    output_path = fetch_pdf_download(identifier, path)
    console.print(f"[green]Downloaded PDF to:[/green] {output_path}")


paper.add_command(paper_comments)
paper.add_command(paper_pdf)
paper.add_command(paper_folders)
