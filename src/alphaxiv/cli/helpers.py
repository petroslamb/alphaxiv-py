"""Shared CLI helpers."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from ..auth import (
    SavedApiKey,
    SavedBrowserAuth,
    ensure_saved_browser_auth,
    fetch_current_user,
    load_api_key_value,
    load_saved_browser_auth,
)
from ..client import AlphaXivClient
from ..exceptions import AlphaXivError
from ..paths import ensure_home_path, get_assistant_context_path, get_context_path
from ..types import AssistantContext, ResolvedPaper
from .messages import alpha_error_to_click_exception, click_error

console = Console()


def run_async(awaitable):
    """Run an async function from the CLI."""
    return asyncio.run(awaitable)


def run_async_with_click_errors(
    awaitable,
    *,
    suggestions: tuple[str, ...] | list[str] = (),
    see_help: str | None = None,
):
    """Run an async function and translate alphaXiv SDK errors into Click errors."""
    try:
        return run_async(awaitable)
    except AlphaXivError as exc:
        raise alpha_error_to_click_exception(
            exc,
            suggestions=suggestions,
            see_help=see_help,
        ) from exc


def make_client() -> AlphaXivClient:
    """Create a client that reuses ALPHAXIV_API_KEY or a saved API key when available."""
    return AlphaXivClient(api_key=load_api_key_value())


def make_assistant_client() -> AlphaXivClient:
    """Create an assistant client that prefers saved browser auth and falls back to an API key."""
    try:
        saved_browser_auth = ensure_saved_browser_auth()
    except Exception:
        saved_browser_auth = load_saved_browser_auth()
    if saved_browser_auth and not saved_browser_auth.is_expired:
        return AlphaXivClient(authorization=saved_browser_auth.authorization_header)
    return make_client()


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
        raise click_error(
            "No current paper is set.",
            suggestions=(
                "alphaxiv context use paper <paper-id>",
                "alphaxiv paper show <paper-id>",
            ),
            see_help="alphaxiv context --help",
        )
    return current.preferred_id


def get_effective_session_id(session_id: str | None) -> str:
    """Use the explicit assistant session id or fall back to saved assistant context."""
    if session_id:
        return session_id
    current = load_assistant_context()
    if not current:
        raise click_error(
            "No current assistant chat is set.",
            suggestions=(
                "alphaxiv assistant list",
                'alphaxiv assistant start "<message>"',
                "alphaxiv context use assistant <session-id>",
            ),
            see_help="alphaxiv assistant --help",
        )
    return current.session_id


def render_context_table(resolved: ResolvedPaper) -> Table:
    table = Table(title="Current Paper Context")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Title", resolved.title or "-")
    table.add_row("arXiv ID", resolved.versionless_id or "-")
    table.add_row("Versioned ID", resolved.canonical_id or "-")
    table.add_row("Version UUID", resolved.version_id or "-")
    table.add_row("Group UUID", resolved.group_id or "-")
    if resolved.input_id and resolved.input_id not in {
        resolved.versionless_id,
        resolved.canonical_id,
        resolved.version_id,
    }:
        table.add_row("Input", resolved.input_id)
    return table


def refresh_api_key_user(saved_api_key: SavedApiKey) -> SavedApiKey:
    """Populate user metadata for env-provided API keys when possible."""
    if saved_api_key.user:
        return saved_api_key
    try:
        user_payload = fetch_current_user(saved_api_key.api_key)
    except Exception:
        return saved_api_key
    return replace(saved_api_key, user=user_payload)


def render_api_key_table(saved_api_key: SavedApiKey) -> Table:
    table = Table(title="alphaXiv API Key")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Status", "configured")
    table.add_row("Source", saved_api_key.source.replace("_", " "))
    table.add_row("Key Prefix", saved_api_key.key_prefix)
    table.add_row("User", saved_api_key.display_name or "-")
    table.add_row("Email", saved_api_key.email or "-")
    table.add_row("User ID", saved_api_key.user_id or "-")
    table.add_row(
        "Saved At",
        "env" if saved_api_key.source == "env" else saved_api_key.saved_at.isoformat(),
    )
    return table


def render_browser_auth_table(saved_auth: SavedBrowserAuth) -> Table:
    table = Table(title="alphaXiv Web Login")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Status", "expired" if saved_auth.is_expired else "configured")
    table.add_row("Source", saved_auth.source.replace("_", " "))
    table.add_row("Kind", saved_auth.kind.replace("_", " "))
    table.add_row("Token Prefix", saved_auth.token_prefix)
    table.add_row("User", saved_auth.display_name or "-")
    table.add_row("Email", saved_auth.email or "-")
    table.add_row("User ID", saved_auth.user_id or "-")
    table.add_row("Created At", saved_auth.created_at.isoformat())
    table.add_row("Expires At", saved_auth.expires_at.isoformat() if saved_auth.expires_at else "-")
    return table


def render_assistant_context_table(context: AssistantContext) -> Table:
    table = Table(title="Current Assistant Context")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Session ID", context.session_id)
    table.add_row("Variant", context.variant)
    table.add_row("Title", context.title or "-")
    table.add_row(
        "Newest Message",
        context.newest_message_at.isoformat() if context.newest_message_at else "-",
    )
    table.add_row("Paper", context.paper.preferred_id if context.paper else "-")
    return table


def print_json(data: Any) -> None:
    console.print_json(data=data)
