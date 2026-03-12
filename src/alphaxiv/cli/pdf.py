"""PDF-related CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from .helpers import console, get_effective_identifier, make_client, run_async

pdf = click.Group("pdf", help="PDF URL and download helpers.")


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


@pdf.command("url")
@click.argument("paper_id", required=False)
def url(paper_id: str | None) -> None:
    """Print the PDF fetch URL for a paper."""
    identifier = get_effective_identifier(paper_id)
    console.print(fetch_pdf_url(identifier))


@pdf.command("download")
@click.argument("args", nargs=-1)
def download(args: tuple[str, ...]) -> None:
    """Download the paper PDF.

    Usage:
      alphaxiv pdf download <path>
      alphaxiv pdf download <paper-id> <path>
    """
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
