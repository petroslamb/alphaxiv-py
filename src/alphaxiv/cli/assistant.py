"""Authenticated assistant CLI commands."""

from __future__ import annotations

import json
from typing import Literal

import click
from rich.table import Table

from ..exceptions import AlphaXivError
from ..types import (
    AssistantContext,
    AssistantMessage,
    AssistantRun,
    AssistantSession,
    AssistantStreamEvent,
    UrlMetadata,
)
from .grouped import WrappedHelpGroup
from .helpers import (
    console,
    get_effective_session_id,
    load_assistant_context,
    load_context,
    make_assistant_client,
    print_json,
    run_async,
    save_assistant_context,
)
from .messages import alpha_error_to_click_exception
from .serialize import (
    reject_raw_and_json,
    serialize_assistant_message,
    serialize_assistant_session,
    serialize_url_metadata,
)

assistant = WrappedHelpGroup(
    "assistant",
    help=(
        "Use the authenticated alphaXiv assistant for paper questions and research chats.\n\n"
        "Use `start` to begin a new chat, `reply` to continue the current chat, `list` and "
        "`history` to inspect saved sessions, and `--paper` when you want the assistant "
        "grounded in one paper.\n\n"
        "Examples:\n"
        "  alphaxiv assistant list\n"
        '  alphaxiv assistant start "Summarize the most important ideas in this paper" --paper 1706.03762\n'
        '  alphaxiv assistant start "Find papers on agent frameworks"\n'
        '  alphaxiv assistant reply "Focus on the most cited ones"'
    ),
)


def _run_with_click_errors(awaitable):
    try:
        return run_async(awaitable)
    except AlphaXivError as exc:
        raise alpha_error_to_click_exception(exc, see_help="alphaxiv assistant --help") from exc


def fetch_sessions(paper_id: str | None = None, limit: int | None = None) -> list[AssistantSession]:
    async def _list() -> list[AssistantSession]:
        async with make_assistant_client() as client:
            return await client.assistant.list(paper_id=paper_id, limit=limit)

    return _run_with_click_errors(_list())


def fetch_history(session_id: str) -> list[AssistantMessage]:
    async def _history() -> list[AssistantMessage]:
        async with make_assistant_client() as client:
            return await client.assistant.history(session_id)

    return _run_with_click_errors(_history())


def set_model_preference(model: str) -> str:
    async def _set() -> str:
        async with make_assistant_client() as client:
            return await client.assistant.set_preferred_model(model)

    return _run_with_click_errors(_set())


def fetch_preferred_model() -> str:
    async def _get() -> str:
        async with make_assistant_client() as client:
            return await client.assistant.preferred_model(refresh=True)

    return _run_with_click_errors(_get())


def fetch_url_metadata(url: str) -> UrlMetadata:
    async def _get() -> UrlMetadata:
        async with make_assistant_client() as client:
            return await client.assistant.url_metadata(url)

    return _run_with_click_errors(_get())


def run_assistant_chat(
    *,
    message: str,
    session_id: str | None = None,
    paper_id: str | None = None,
    model: str | None = None,
    thinking: bool = True,
    web_search: Literal["off", "full"] = "off",
    raw: bool = False,
) -> AssistantRun:
    state = {
        "raw": raw,
        "started_answer": False,
        "printed_thinking": False,
        "printed_newline_after_answer": False,
    }

    def render_event(event: AssistantStreamEvent) -> None:
        if state["raw"]:
            print_json(event.raw)
            return

        if event.event_type == "delta_output_reasoning":
            if not state["printed_thinking"]:
                console.print("[dim]Thinking...[/dim]")
                state["printed_thinking"] = True
            return

        if event.event_type == "tool_use":
            query_text = None
            if event.content:
                try:
                    payload = json.loads(event.content)
                except json.JSONDecodeError:
                    payload = None
                if isinstance(payload, dict) and payload.get("query"):
                    query_text = str(payload["query"])
            label = event.kind or "Tool"
            if query_text:
                console.print(f"[cyan]{label}[/cyan]: {query_text}")
            else:
                console.print(f"[cyan]{label}[/cyan]")
            return

        if event.event_type == "tool_result_text":
            preview = (event.content or "").strip().splitlines()
            if preview:
                console.print(f"[dim]Result:[/dim] {preview[0][:140]}")
            return

        if event.event_type == "delta_output_text" and event.delta:
            if not state["started_answer"]:
                console.print("[bold]Assistant[/bold]")
                state["started_answer"] = True
            console.print(event.delta, end="")
            state["printed_newline_after_answer"] = False
            return

        if event.event_type == "error":
            message_text = event.error_message or "alphaXiv assistant returned an error."
            if not state["printed_newline_after_answer"] and state["started_answer"]:
                console.print()
            console.print(f"[red]{message_text}[/red]")
            state["printed_newline_after_answer"] = True

    async def _run() -> AssistantRun:
        async with make_assistant_client() as client:
            return await client.assistant.ask(
                message,
                session_id=session_id,
                paper_id=paper_id,
                model=model,
                thinking=thinking,
                web_search=web_search,
                on_event=render_event,
            )

    run = _run_with_click_errors(_run())
    if not raw and run.output_text and not state["printed_newline_after_answer"]:
        console.print()
    return run


def resolve_context_for_session(session_id: str) -> AssistantContext:
    current_paper = load_context()
    homepage_sessions = fetch_sessions()
    for session in homepage_sessions:
        if session.id == session_id:
            return AssistantContext(
                session_id=session.id,
                variant="homepage",
                paper=None,
                newest_message_at=session.newest_message_at,
                title=session.title,
            )

    if current_paper:
        paper_sessions = fetch_sessions(current_paper.preferred_id)
        for session in paper_sessions:
            if session.id == session_id:
                return AssistantContext(
                    session_id=session.id,
                    variant="paper",
                    paper=current_paper,
                    newest_message_at=session.newest_message_at,
                    title=session.title,
                )

    history = fetch_history(session_id)
    newest_message_at = max(
        (message.selected_at for message in history if message.selected_at is not None),
        default=None,
    )
    return AssistantContext(
        session_id=session_id,
        variant="homepage",
        paper=None,
        newest_message_at=newest_message_at,
        title=None,
    )


def _save_run_context(run: AssistantRun) -> None:
    if not run.session_id:
        return
    context = AssistantContext(
        session_id=run.session_id,
        variant=run.variant,
        paper=run.paper,
        newest_message_at=run.newest_message_at,
        title=run.session_title,
    )
    save_assistant_context(context)


def _message_sort_key(message: AssistantMessage) -> tuple[float, str]:
    if message.selected_at is None:
        return (-1.0, message.id)
    return (message.selected_at.timestamp(), message.id)


@assistant.command("list")
@click.option(
    "--paper",
    "paper_id",
    default=None,
    help="Restrict the listing to chats associated with one paper.",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    show_default=True,
    help="Maximum number of sessions to print after sorting by newest message.",
)
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def list_sessions(paper_id: str | None, limit: int, json_output: bool) -> None:
    """List saved assistant chats for the homepage or for one paper."""
    sessions = fetch_sessions(paper_id=paper_id, limit=limit)
    if json_output:
        print_json(
            {
                "paper_id": paper_id,
                "limit": limit,
                "sessions": [serialize_assistant_session(session) for session in sessions],
            }
        )
        return
    title = "Paper Assistant Sessions" if paper_id else "Homepage Assistant Sessions"
    table = Table(title=title)
    table.add_column("Session ID")
    table.add_column("Title")
    table.add_column("Newest Message")
    for session in sessions:
        table.add_row(
            session.id,
            session.title or "-",
            session.newest_message_at.isoformat() if session.newest_message_at else "-",
        )
    console.print(table)


@assistant.command("set-model")
@click.argument("model")
def set_model(model: str) -> None:
    """Save the preferred assistant model in alphaXiv user preferences."""
    selected = set_model_preference(model)
    console.print(f"[green]Preferred assistant model set:[/green] {selected}")


@assistant.command("model")
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def show_model(json_output: bool) -> None:
    """Show the preferred assistant model currently stored in alphaXiv."""
    model = fetch_preferred_model()
    if json_output:
        print_json({"model": model})
        return
    console.print(f"[bold]Preferred assistant model:[/bold] {model}")


@assistant.command("url-metadata")
@click.argument("url")
@click.option("--raw", is_flag=True, help="Print the raw metadata JSON payload.")
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def show_url_metadata(url: str, raw: bool, json_output: bool) -> None:
    """Fetch the assistant's link-preview metadata for one URL.

    Use this when you want the assistant's title/description preview for a link before
    discussing or sharing it in a chat.
    """
    reject_raw_and_json(raw, json_output, see_help="alphaxiv assistant url-metadata --help")
    metadata = fetch_url_metadata(url)
    if raw:
        print_json(metadata.raw)
        return
    if json_output:
        print_json(serialize_url_metadata(metadata))
        return
    table = Table(title="Assistant URL Metadata")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("URL", metadata.url)
    table.add_row("Title", metadata.title or "-")
    table.add_row("Description", metadata.description or "-")
    table.add_row("Site", metadata.site_name or "-")
    table.add_row("Author", metadata.author or "-")
    table.add_row("Image", metadata.image_url or "-")
    table.add_row("Favicon", metadata.favicon or "-")
    console.print(table)


@assistant.command("start")
@click.argument("message")
@click.option(
    "--paper",
    "paper_id",
    default=None,
    help="Ground the new chat in one paper by resolving the paper id first.",
)
@click.option(
    "--model",
    default=None,
    help="Use a one-off assistant model label or wire id for this chat only.",
)
@click.option(
    "--web-search",
    type=click.Choice(["off", "full"], case_sensitive=False),
    default="off",
    show_default=True,
    help="Allow alphaXiv web search during this chat.",
)
@click.option(
    "--thinking/--no-thinking",
    default=True,
    show_default=True,
    help="Show reasoning-status events while the assistant is working.",
)
@click.option("--raw", is_flag=True, help="Print raw SSE event payloads.")
def start_chat(
    message: str,
    paper_id: str | None,
    model: str | None,
    web_search: Literal["off", "full"],
    thinking: bool,
    raw: bool,
) -> None:
    """Start a new assistant chat and save it as the current session.

    Use `start` to begin a fresh conversation. Use `reply` when you want to continue the
    saved current chat or target an existing session id.
    """
    run = run_assistant_chat(
        message=message,
        paper_id=paper_id,
        model=model,
        thinking=thinking,
        web_search=web_search,
        raw=raw,
    )
    _save_run_context(run)
    if run.session_id:
        console.print(f"[green]Current assistant chat set:[/green] {run.session_id}")
    if run.error_message and not raw:
        raise click.ClickException(run.error_message)


@assistant.command("reply")
@click.argument("parts", nargs=-1, required=True)
@click.option(
    "--web-search",
    type=click.Choice(["off", "full"], case_sensitive=False),
    default="off",
    show_default=True,
    help="Allow alphaXiv web search during this reply.",
)
@click.option(
    "--model",
    default=None,
    help="Use a one-off assistant model label or wire id for this reply only.",
)
@click.option(
    "--thinking/--no-thinking",
    default=True,
    show_default=True,
    help="Show reasoning-status events while the assistant is working.",
)
@click.option("--raw", is_flag=True, help="Print raw SSE event payloads.")
def reply_chat(
    parts: tuple[str, ...],
    web_search: Literal["off", "full"],
    model: str | None,
    thinking: bool,
    raw: bool,
) -> None:
    """Continue the current chat, or reply to an explicit session id first.

    Use `reply` after `assistant start` or after selecting a chat with
    `context use assistant`. Use `start` if you want a new conversation.
    """
    if len(parts) == 1:
        session_id = None
        message = parts[0]
    else:
        session_id = parts[0]
        message = " ".join(parts[1:])

    effective_session_id = get_effective_session_id(session_id)
    assistant_context = load_assistant_context()
    paper_id = None
    if (
        assistant_context
        and assistant_context.session_id == effective_session_id
        and assistant_context.paper
    ):
        paper_id = assistant_context.paper.preferred_id

    run = run_assistant_chat(
        message=message,
        session_id=effective_session_id,
        paper_id=paper_id,
        model=model,
        thinking=thinking,
        web_search=web_search,
        raw=raw,
    )
    _save_run_context(run)
    if run.error_message and not raw:
        raise click.ClickException(run.error_message)


@assistant.command("history")
@click.argument("session_id", required=False)
@click.option("--raw", is_flag=True, help="Print raw message payloads.")
@click.option("--json", "json_output", is_flag=True, help="Print normalized machine-readable JSON.")
def show_history(session_id: str | None, raw: bool, json_output: bool) -> None:
    """Show the full message history for the current or selected assistant chat.

    Use this when you need the full transcript of a saved assistant session instead of
    sending a new message.
    """
    reject_raw_and_json(raw, json_output, see_help="alphaxiv assistant history --help")
    effective_session_id = get_effective_session_id(session_id)
    history = fetch_history(effective_session_id)
    if raw:
        print_json([message.raw for message in history])
        return
    if json_output:
        print_json(
            {
                "session_id": effective_session_id,
                "messages": [serialize_assistant_message(message) for message in history],
            }
        )
        return

    console.print(f"[bold]Assistant History[/bold] {effective_session_id}")
    for message in sorted(history, key=_message_sort_key):
        if message.message_type == "input_text":
            console.print(f"\n[bold]User[/bold]\n{message.content or ''}")
        elif message.message_type == "output_text":
            console.print(f"\n[bold]Assistant[/bold]\n{message.content or ''}")
        elif message.message_type == "output_reasoning":
            console.print(f"\n[dim]Thinking[/dim]\n{message.content or ''}")
        elif message.message_type == "tool_use":
            label = message.kind or "Tool"
            query = message.content or ""
            console.print(f"\n[cyan]{label}[/cyan]\n{query}")
        elif message.message_type == "tool_result_text":
            console.print(f"\n[dim]Tool Result[/dim]\n{message.content or ''}")
        else:
            console.print(f"\n[dim]{message.message_type}[/dim]\n{message.content or ''}")
