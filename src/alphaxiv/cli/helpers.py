"""Shared CLI helpers."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from ..auth import SavedAuth, load_authorization
from ..client import AlphaXivClient
from ..paths import ensure_home_path, get_assistant_context_path, get_context_path
from ..types import AssistantContext, ResolvedPaper

console = Console()


def run_async(awaitable):
    """Run an async function from the CLI."""
    return asyncio.run(awaitable)


def make_client() -> AlphaXivClient:
    """Create a client that reuses ALPHAXIV_API_KEY or saved auth when available."""
    return AlphaXivClient(authorization=load_authorization())


def load_context() -> ResolvedPaper | None:
    """Load the current paper context from disk."""
    path = get_context_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    return ResolvedPaper.from_dict(data)


def load_assistant_context() -> AssistantContext | None:
    """Load the current assistant session context from disk."""
    path = get_assistant_context_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not data.get("session_id"):
        return None
    return AssistantContext.from_dict(data)


def save_context(resolved: ResolvedPaper) -> Path:
    """Persist the current paper context."""
    ensure_home_path()
    path = get_context_path()
    path.write_text(json.dumps(resolved.to_dict(), indent=2))
    return path


def save_assistant_context(context: AssistantContext) -> Path:
    """Persist the current assistant session context."""
    ensure_home_path()
    path = get_assistant_context_path()
    path.write_text(json.dumps(context.to_dict(), indent=2))
    return path


def clear_context() -> None:
    """Remove the current paper context file."""
    path = get_context_path()
    if path.exists():
        path.unlink()


def clear_assistant_context() -> None:
    """Remove the current assistant session context file."""
    path = get_assistant_context_path()
    if path.exists():
        path.unlink()


def get_effective_identifier(paper_id: str | None) -> str:
    """Use the explicit paper id or fall back to saved context."""
    if paper_id:
        return paper_id
    current = load_context()
    if not current:
        raise click.ClickException(
            "No current paper is set. Run 'alphaxiv use <paper-id>' or pass a paper id explicitly."
        )
    return current.preferred_id


def get_effective_session_id(session_id: str | None) -> str:
    """Use the explicit assistant session id or fall back to saved assistant context."""
    if session_id:
        return session_id
    current = load_assistant_context()
    if not current:
        raise click.ClickException(
            "No current assistant chat is set. Run 'alphaxiv assistant use <session-id>' "
            "or start a chat first."
        )
    return current.session_id


def render_context_table(resolved: ResolvedPaper) -> Table:
    table = Table(title="Current alphaXiv Context")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Input ID", resolved.input_id or "-")
    table.add_row("Bare ID", resolved.versionless_id or "-")
    table.add_row("Canonical ID", resolved.canonical_id or "-")
    table.add_row("Version UUID", resolved.version_id or "-")
    table.add_row("Group UUID", resolved.group_id or "-")
    return table


def render_auth_table(saved_auth: SavedAuth, preferred_model: str | None = None) -> Table:
    table = Table(title="alphaXiv Authentication")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Status", "expired" if saved_auth.is_expired else "authenticated")
    table.add_row("Source", saved_auth.source.replace("_", " "))
    table.add_row("Kind", saved_auth.kind.replace("_", " "))
    table.add_row("User", saved_auth.display_name or "-")
    table.add_row("Email", saved_auth.email or "-")
    table.add_row("User ID", saved_auth.user_id or "-")
    table.add_row("Preferred Model", preferred_model or "-")
    table.add_row(
        "Saved At", "env" if saved_auth.source == "env" else saved_auth.created_at.isoformat()
    )
    table.add_row(
        "Expires At",
        saved_auth.expires_at.isoformat() if saved_auth.expires_at else "-",
    )
    return table


def render_assistant_context_table(context: AssistantContext) -> Table:
    table = Table(title="Current alphaXiv Assistant")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Session ID", context.session_id)
    table.add_row("Variant", context.variant)
    table.add_row("Title", context.title or "-")
    table.add_row(
        "Newest Message",
        context.newest_message_at.isoformat() if context.newest_message_at else "-",
    )
    table.add_row(
        "Paper",
        context.paper.preferred_id if context.paper else "-",
    )
    return table


def print_json(data: Any) -> None:
    console.print_json(data=data)
