"""API-key management CLI commands."""

from __future__ import annotations

import click

from ..auth import (
    ALPHAXIV_API_KEY_ENV,
    authenticate_with_api_key,
    clear_saved_api_key,
    resolve_api_key,
    save_api_key,
)
from ..paths import get_api_key_path
from .grouped import WrappedHelpGroup
from .helpers import console, refresh_api_key_user, render_api_key_table

auth = WrappedHelpGroup(
    "auth",
    help="Validate, inspect, and clear the alphaXiv API key used by the CLI.",
)


def _load_display_api_key():
    saved_api_key = resolve_api_key()
    if not saved_api_key:
        return None
    return refresh_api_key_user(saved_api_key)


@auth.command("set-api-key")
@click.option(
    "--api-key",
    help="Explicit alphaXiv API key to validate and save. Prompts securely if omitted.",
)
def set_api_key(api_key: str | None) -> None:
    """Validate an API key against alphaXiv and store it in api-key.json."""
    resolved_api_key = api_key
    if resolved_api_key is None:
        resolved_api_key = click.prompt("alphaXiv API key", hide_input=True)
    try:
        saved_api_key = authenticate_with_api_key(resolved_api_key)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    path = save_api_key(saved_api_key)
    console.print(f"[green]API key saved:[/green] {path}")
    if saved_api_key.display_name or saved_api_key.email:
        console.print(
            f"[dim]Authenticated as {saved_api_key.display_name or saved_api_key.email}"
            f"{f' <{saved_api_key.email}>' if saved_api_key.display_name and saved_api_key.email else ''}[/dim]"
        )


@auth.command("status")
def status() -> None:
    """Show which API key source is active and who it resolves to."""
    saved_api_key = _load_display_api_key()
    if saved_api_key:
        console.print(render_api_key_table(saved_api_key))
    else:
        console.print("[yellow]No alphaXiv API key is configured.[/yellow]")
        console.print(
            f"[dim]Set {ALPHAXIV_API_KEY_ENV} or run 'alphaxiv auth set-api-key'. "
            f"Local key path: {get_api_key_path()}[/dim]"
        )


@auth.command("clear")
def clear() -> None:
    """Remove the saved local API key."""
    had_api_key = get_api_key_path().exists()
    clear_saved_api_key()
    if had_api_key:
        console.print("[green]Removed local alphaXiv API key.[/green]")
    else:
        console.print("[yellow]No local alphaXiv API key was present.[/yellow]")
    console.print(f"[dim]API key path: {get_api_key_path()}[/dim]")
