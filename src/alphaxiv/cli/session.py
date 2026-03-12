"""Session-like CLI commands for current paper context."""

from __future__ import annotations

import click

from ..auth import (
    ALPHAXIV_API_KEY_ENV,
    authenticate_with_api_key,
    authenticate_with_browser,
    clear_saved_auth,
    ensure_saved_auth,
    save_auth,
)
from ..paths import (
    get_assistant_context_path,
    get_auth_path,
    get_browser_profile_path,
    get_context_path,
)
from ..types import ResolvedPaper
from .helpers import (
    clear_assistant_context,
    clear_context,
    console,
    load_assistant_context,
    load_context,
    make_client,
    render_assistant_context_table,
    render_auth_table,
    render_context_table,
    run_async,
    save_context,
)


def resolve_paper_identifier(identifier: str) -> ResolvedPaper:
    async def _resolve() -> ResolvedPaper:
        async with make_client() as client:
            return await client.papers.resolve(identifier)

    return run_async(_resolve())


def _saved_preferred_model(saved_auth) -> str | None:
    preferences = saved_auth.user.get("preferences") if isinstance(saved_auth.user, dict) else None
    if not isinstance(preferences, dict):
        return None
    base = preferences.get("base")
    if not isinstance(base, dict):
        return None
    model = base.get("preferredLlmModel")
    return model.strip() if isinstance(model, str) and model.strip() else None


def fetch_preferred_model(saved_auth) -> str | None:
    async def _preferred() -> str:
        async with make_client() as client:
            return await client.assistant.preferred_model(refresh=True)

    try:
        return run_async(_preferred())
    except Exception:
        return _saved_preferred_model(saved_auth)


def register_session_commands(cli):
    @cli.command("login")
    @click.option(
        "--api-key",
        help="Save an explicit alphaXiv API key instead of opening the browser login flow.",
    )
    def login(api_key: str | None) -> None:
        """Save alphaXiv authentication locally."""
        if api_key:
            try:
                saved_auth = authenticate_with_api_key(api_key)
            except Exception as exc:
                raise click.ClickException(str(exc)) from exc
        else:
            console.print("[yellow]Opening browser for alphaXiv sign-in...[/yellow]")
            console.print(f"[dim]Using persistent profile: {get_browser_profile_path()}[/dim]")
            console.print()
            console.print("[bold]Instructions[/bold]")
            console.print(
                "1. In the browser, use Continue with Google or any other alphaXiv sign-in path."
            )
            console.print("2. Wait until the alphaXiv session is fully loaded.")
            console.print("3. Press ENTER back in the terminal to save the current bearer token.")
            console.print()
            try:
                saved_auth = authenticate_with_browser()
            except Exception as exc:
                raise click.ClickException(str(exc)) from exc

        path = save_auth(saved_auth)
        console.print(f"[green]Authentication saved:[/green] {path}")
        if saved_auth.display_name or saved_auth.email:
            console.print(
                f"[dim]Logged in as {saved_auth.display_name or saved_auth.email}"
                f"{f' <{saved_auth.email}>' if saved_auth.display_name and saved_auth.email else ''}[/dim]"
            )

    @cli.command("logout")
    @click.option(
        "--clear-browser-profile",
        is_flag=True,
        help="Also remove the saved Playwright browser profile under ALPHAXIV_HOME.",
    )
    def logout(clear_browser_profile: bool) -> None:
        """Remove saved alphaXiv authentication."""
        clear_saved_auth(clear_browser_profile=clear_browser_profile)
        console.print("[green]Removed saved alphaXiv authentication.[/green]")
        console.print(f"[dim]Auth file: {get_auth_path()}[/dim]")
        if clear_browser_profile:
            console.print(f"[dim]Browser profile removed: {get_browser_profile_path()}[/dim]")

    @cli.command("use")
    @click.argument("paper_id")
    def use_paper(paper_id: str) -> None:
        """Set the current paper context."""
        resolved = resolve_paper_identifier(paper_id)
        path = save_context(resolved)
        console.print(f"[green]Current paper set:[/green] {resolved.preferred_id}")
        console.print(f"[dim]Context saved to {path}[/dim]")

    @cli.command("status")
    def status() -> None:
        """Show saved auth and current paper context."""
        saved_auth = ensure_saved_auth()
        if saved_auth:
            console.print(render_auth_table(saved_auth, fetch_preferred_model(saved_auth)))
        else:
            console.print("[yellow]Not logged in to alphaXiv.[/yellow]")
            console.print(
                f"[dim]Set {ALPHAXIV_API_KEY_ENV} or save auth to {get_auth_path()}[/dim]"
            )

        resolved = load_context()
        assistant_context = load_assistant_context()
        if resolved:
            console.print()
            console.print(render_context_table(resolved))
        else:
            console.print()
            console.print("[yellow]No current paper is set.[/yellow]")
            console.print(f"[dim]Expected context file: {get_context_path()}[/dim]")

        if assistant_context:
            console.print()
            console.print(render_assistant_context_table(assistant_context))
        else:
            console.print()
            console.print("[yellow]No current assistant chat is set.[/yellow]")
            console.print(
                f"[dim]Expected assistant context file: {get_assistant_context_path()}[/dim]"
            )

    @cli.command("clear")
    def clear() -> None:
        """Clear the current paper context."""
        clear_context()
        console.print("[green]Cleared current paper context.[/green]")
        if load_assistant_context():
            clear_assistant_context()
            console.print("[green]Cleared current assistant chat context.[/green]")
