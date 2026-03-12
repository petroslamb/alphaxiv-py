"""CLI entrypoint for alphaxiv-py."""

from __future__ import annotations

import click

from . import __version__
from .cli import (
    assistant,
    feed,
    paper,
    pdf,
    register_explore_commands,
    register_paper_commands,
    register_session_commands,
)
from .cli.grouped import SectionedGroup


@click.group(cls=SectionedGroup)
@click.version_option(version=__version__, prog_name="alphaXiv CLI")
def cli() -> None:
    """alphaXiv CLI."""


register_session_commands(cli)
register_explore_commands(cli)
register_paper_commands(cli)
cli.add_command(assistant)
cli.add_command(feed)
cli.add_command(paper)
cli.add_command(pdf)


def main() -> None:
    cli()
