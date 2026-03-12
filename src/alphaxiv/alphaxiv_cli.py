"""CLI entrypoint for alphaxiv-py."""

from __future__ import annotations

import click

from . import __version__
from .cli import assistant, auth, context, feed, folders, paper, search
from .cli.grouped import WrappedHelpGroup


@click.group(cls=WrappedHelpGroup)
@click.version_option(version=__version__, prog_name="alphaXiv CLI")
def cli() -> None:
    """Explore alphaXiv public APIs and authenticated assistant features."""


cli.add_command(auth)
cli.add_command(context)
cli.add_command(search)
cli.add_command(feed)
cli.add_command(paper)
cli.add_command(assistant)
cli.add_command(folders)


def main() -> None:
    cli()
