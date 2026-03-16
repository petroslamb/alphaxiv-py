"""CLI entrypoint for alphaxiv-py."""

from __future__ import annotations

import click

from . import __version__
from .cli import agent, assistant, auth, context, feed, folders, guide, paper, search, skill
from .cli.grouped import WrappedHelpGroup


@click.group(cls=WrappedHelpGroup)
@click.version_option(version=__version__, prog_name="alphaXiv CLI")
def cli() -> None:
    """Explore alphaXiv from the terminal.

    Typical workflow: use `search` or `feed` to discover papers, `paper` to inspect
    metadata and full text, `assistant` to ask follow-up questions, and `context`
    to save the current paper or assistant session between commands. Use `guide`
    for task-level workflows and `skill` to install packaged agent integrations.
    """


cli.add_command(auth)
cli.add_command(context)
cli.add_command(search)
cli.add_command(feed)
cli.add_command(paper)
cli.add_command(assistant)
cli.add_command(folders)
cli.add_command(guide)
cli.add_command(skill)
cli.add_command(agent)


def main() -> None:
    cli()
