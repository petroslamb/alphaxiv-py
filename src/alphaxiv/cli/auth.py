"""Authentication management CLI commands."""

from __future__ import annotations

import click

from ..auth import (
    ALPHAXIV_API_KEY_ENV,
    authenticate_with_api_key,
    authenticate_with_browser,
    clear_saved_api_key,
    clear_saved_browser_auth,
    ensure_saved_browser_auth,
    load_saved_browser_auth,
    resolve_api_key,
    save_api_key,
    save_browser_auth,
)
from ..paths import get_api_key_path, get_browser_auth_path, get_browser_profile_path
from .grouped import WrappedHelpGroup
from .helpers import (
    console,
    refresh_api_key_user,
    render_api_key_table,
    render_browser_auth_table,
)

auth = WrappedHelpGroup(
    "auth",
    help=(
        "Configure API-key auth and optional browser-backed assistant auth.\n\n"
        "Examples:\n"
        "  alphaxiv auth set-api-key\n"
        "  alphaxiv auth login-web\n"
        "  alphaxiv auth status\n"
        "  alphaxiv auth clear\n"
        "  alphaxiv auth clear-web --clear-browser-profile"
    ),
)


def _load_display_api_key():
    saved_api_key = resolve_api_key()
    if not saved_api_key:
        return None
    return refresh_api_key_user(saved_api_key)


def _load_display_browser_auth():
    try:
        return ensure_saved_browser_auth()
    except Exception:
        return load_saved_browser_auth()


@auth.command("set-api-key")
@click.option(
    "--api-key",
    help="Explicit alphaXiv API key to validate and save. Prompts securely if omitted.",
)
def set_api_key(api_key: str | None) -> None:
    """Validate an API key and store it locally for future CLI commands."""
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


@auth.command("login-web")
def login_web() -> None:
    """Log in through the alphaXiv web app and save the resulting browser auth."""
    console.print("[yellow]Opening browser for alphaXiv sign-in...[/yellow]")
    console.print(f"[dim]Using persistent profile: {get_browser_profile_path()}[/dim]")
    console.print()
    console.print("[bold]Instructions[/bold]")
    console.print("1. Complete the alphaXiv sign-in flow in the browser window.")
    console.print("2. Wait until the alphaXiv session is fully loaded.")
    console.print("3. Press ENTER back in the terminal to save the browser-backed auth.")
    console.print()
    try:
        saved_auth = authenticate_with_browser()
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    path = save_browser_auth(saved_auth)
    console.print(f"[green]Browser auth saved:[/green] {path}")
    if saved_auth.display_name or saved_auth.email:
        console.print(
            f"[dim]Logged in as {saved_auth.display_name or saved_auth.email}"
            f"{f' <{saved_auth.email}>' if saved_auth.display_name and saved_auth.email else ''}[/dim]"
        )


@auth.command("status")
def status() -> None:
    """Show the saved API-key auth and browser-backed auth state."""
    saved_api_key = _load_display_api_key()
    saved_browser_auth = _load_display_browser_auth()

    if saved_api_key:
        console.print(render_api_key_table(saved_api_key))
    else:
        console.print("[yellow]No alphaXiv API key is configured.[/yellow]")
        console.print(
            f"[dim]Set {ALPHAXIV_API_KEY_ENV} or run 'alphaxiv auth set-api-key'. "
            f"Local key path: {get_api_key_path()}[/dim]"
        )

    console.print()
    if saved_browser_auth:
        console.print(render_browser_auth_table(saved_browser_auth))
    else:
        console.print("[yellow]No alphaXiv web login is configured.[/yellow]")
        console.print(f"[dim]Browser auth path: {get_browser_auth_path()}[/dim]")
        if get_browser_profile_path().exists():
            console.print(
                "[dim]A browser profile exists. Run 'alphaxiv auth login-web' to refresh and save "
                "browser-backed auth.[/dim]"
            )
        else:
            console.print(
                "[dim]Run 'alphaxiv auth login-web' if you need assistant access through the web "
                "session.[/dim]"
            )

    if saved_browser_auth:
        console.print()
        console.print("[dim]Assistant commands prefer saved web login when it is available.[/dim]")


@auth.command("clear")
def clear() -> None:
    """Remove the saved local API key from disk."""
    had_api_key = get_api_key_path().exists()
    clear_saved_api_key()
    if had_api_key:
        console.print("[green]Removed local alphaXiv API key.[/green]")
    else:
        console.print("[yellow]No local alphaXiv API key was present.[/yellow]")
    console.print(f"[dim]API key path: {get_api_key_path()}[/dim]")


@auth.command("clear-web")
@click.option(
    "--clear-browser-profile",
    is_flag=True,
    help="Also remove the saved Playwright browser profile under ALPHAXIV_HOME.",
)
def clear_web(clear_browser_profile: bool) -> None:
    """Remove the saved browser-backed auth used by assistant commands."""
    had_browser_auth = get_browser_auth_path().exists()
    had_browser_profile = get_browser_profile_path().exists()
    clear_saved_browser_auth(clear_browser_profile=clear_browser_profile)
    if had_browser_auth:
        console.print("[green]Removed saved alphaXiv web login.[/green]")
    else:
        console.print("[yellow]No saved alphaXiv web login was present.[/yellow]")
    console.print(f"[dim]Browser auth path: {get_browser_auth_path()}[/dim]")
    if clear_browser_profile:
        if had_browser_profile:
            console.print(f"[dim]Browser profile removed: {get_browser_profile_path()}[/dim]")
        else:
            console.print(
                f"[dim]Browser profile was already absent: {get_browser_profile_path()}[/dim]"
            )
