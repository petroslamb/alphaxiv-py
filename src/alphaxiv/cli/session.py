"""Saved paper and assistant context commands."""

from __future__ import annotations

from dataclasses import replace

import click

from ..paths import get_assistant_context_path, get_context_path
from ..types import ResolvedPaper
from .grouped import WrappedHelpGroup
from .helpers import (
    clear_assistant_context,
    clear_context,
    console,
    load_assistant_context,
    load_context,
    make_client,
    print_json,
    render_assistant_context_table,
    render_context_table,
    run_async,
    save_assistant_context,
    save_context,
)
from .serialize import serialize_assistant_context, serialize_resolved_paper

context = WrappedHelpGroup(
    "context",
    help=(
        "Inspect or update the saved paper and assistant context.\n\n"
        "Many `paper` commands can omit `[paper-id]` if a current paper is saved here. "
        "Assistant replies can also continue the saved current chat.\n\n"
        "Examples:\n"
        "  alphaxiv context show\n"
        "  alphaxiv context use paper 1706.03762\n"
        "  alphaxiv context clear paper\n"
        "  alphaxiv context use assistant session-existing"
    ),
)


def resolve_paper_identifier(identifier: str) -> ResolvedPaper:
    async def _resolve() -> ResolvedPaper:
        async with make_client() as client:
            return await client.papers.resolve(identifier)

    return run_async(_resolve())


def hydrate_paper_context_title(resolved: ResolvedPaper) -> ResolvedPaper:
    if resolved.title or not (resolved.canonical_id or resolved.versionless_id):
        return resolved

    identifier = resolved.canonical_id or resolved.versionless_id
    if identifier is None:
        return resolved

    async def _fetch_title() -> str | None:
        async with make_client() as client:
            paper = await client.papers.get(identifier)
            title = paper.version.title.strip()
            return title or None

    try:
        title = run_async(_fetch_title())
    except Exception:
        return resolved

    if not title:
        return resolved

    hydrated = replace(resolved, title=title)
    save_context(hydrated)
    return hydrated


def _show_missing_paper_context() -> None:
    console.print("[bold]Current Paper Context[/bold]")
    console.print("[yellow]No current paper is set.[/yellow]")
    console.print(f"[dim]Expected paper context file: {get_context_path()}[/dim]")


def _show_missing_assistant_context() -> None:
    console.print("[bold]Current Assistant Context[/bold]")
    console.print("[yellow]No current assistant chat is set.[/yellow]")
    console.print(f"[dim]Expected assistant context file: {get_assistant_context_path()}[/dim]")


def _resolved_current_paper() -> ResolvedPaper | None:
    resolved = load_context()
    if not resolved:
        return None
    return hydrate_paper_context_title(resolved)


def _show_paper_context() -> None:
    resolved = _resolved_current_paper()
    if not resolved:
        _show_missing_paper_context()
        return
    console.print(render_context_table(resolved))


def _show_assistant_context() -> None:
    assistant_context = load_assistant_context()
    if not assistant_context:
        _show_missing_assistant_context()
        return
    console.print(render_assistant_context_table(assistant_context))


@context.group("show", cls=WrappedHelpGroup, invoke_without_command=True)
@click.pass_context
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def show_group(ctx: click.Context, json_output: bool) -> None:
    """Show the saved paper context, assistant context, or both together."""
    if ctx.invoked_subcommand is not None:
        return
    if json_output:
        print_json(
            {
                "paper": serialize_resolved_paper(_resolved_current_paper()),
                "assistant": serialize_assistant_context(load_assistant_context()),
            }
        )
        return
    _show_paper_context()
    console.print()
    _show_assistant_context()


@show_group.command("paper")
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def show_paper_context(json_output: bool) -> None:
    """Show only the saved current paper, including title and resolved ids."""
    if json_output:
        print_json(serialize_resolved_paper(_resolved_current_paper()))
        return
    _show_paper_context()


@show_group.command("assistant")
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def show_assistant_context(json_output: bool) -> None:
    """Show only the saved current assistant session."""
    if json_output:
        print_json(serialize_assistant_context(load_assistant_context()))
        return
    _show_assistant_context()


@context.group("use", cls=WrappedHelpGroup)
def use_group() -> None:
    """Set the saved current paper or current assistant session."""


@use_group.command("paper")
@click.argument("paper_id")
def use_paper_context(paper_id: str) -> None:
    """Resolve a paper id and save it as the default paper for later commands."""
    resolved = resolve_paper_identifier(paper_id)
    path = save_context(resolved)
    console.print(f"[green]Current paper set:[/green] {resolved.preferred_id}")
    console.print(f"[dim]Paper context saved to {path}[/dim]")


@use_group.command("assistant")
@click.argument("session_id")
def use_assistant_context(session_id: str) -> None:
    """Save an assistant session id as the default chat for later replies."""
    from .assistant import resolve_context_for_session

    resolved = resolve_context_for_session(session_id)
    path = save_assistant_context(resolved)
    console.print(f"[green]Current assistant chat set:[/green] {resolved.session_id}")
    console.print(f"[dim]Assistant context saved to {path}[/dim]")


def _clear_paper_context() -> bool:
    had_context = get_context_path().exists()
    clear_context()
    return had_context


def _clear_assistant_chat_context() -> bool:
    had_context = get_assistant_context_path().exists()
    clear_assistant_context()
    return had_context


def _print_clear_result(*, cleared_paper: bool, cleared_assistant: bool) -> None:
    if cleared_paper:
        console.print("[green]Cleared current paper context.[/green]")
    if cleared_assistant:
        console.print("[green]Cleared current assistant chat context.[/green]")
    if not cleared_paper and not cleared_assistant:
        console.print("[yellow]No saved paper or assistant context was present.[/yellow]")


@context.group("clear", cls=WrappedHelpGroup, invoke_without_command=True)
@click.pass_context
def clear_group(ctx: click.Context) -> None:
    """Clear the saved paper context, assistant context, or both together."""
    if ctx.invoked_subcommand is not None:
        return
    _print_clear_result(
        cleared_paper=_clear_paper_context(),
        cleared_assistant=_clear_assistant_chat_context(),
    )


@clear_group.command("paper")
def clear_paper_context() -> None:
    """Clear only the saved current paper."""
    _print_clear_result(cleared_paper=_clear_paper_context(), cleared_assistant=False)


@clear_group.command("assistant")
def clear_assistant_context_command() -> None:
    """Clear only the saved current assistant session."""
    _print_clear_result(cleared_paper=False, cleared_assistant=_clear_assistant_chat_context())
