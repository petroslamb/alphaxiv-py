"""Shared CLI error and suggestion formatting."""

from __future__ import annotations

from collections.abc import Sequence

import click

from ..exceptions import AlphaXivError, AuthRequiredError

AUTH_HELP_PATH = "alphaxiv auth --help"
AUTH_TRY_COMMANDS = (
    "alphaxiv auth set-api-key",
    "alphaxiv auth status",
)


def _unique_items(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def format_cli_message(
    message: str,
    *,
    suggestions: Sequence[str] = (),
    see_help: str | None = None,
) -> str:
    """Format a CLI error/help message with optional suggestions."""
    lines = [message.strip()]
    cleaned_suggestions = _unique_items(suggestions)
    if cleaned_suggestions:
        lines.append("")
        lines.append("Try:")
        lines.extend(f"  {item}" for item in cleaned_suggestions)
    if see_help:
        lines.append("")
        lines.append(f"See: {see_help}")
    return "\n".join(lines)


def click_error(
    message: str,
    *,
    suggestions: Sequence[str] = (),
    see_help: str | None = None,
) -> click.ClickException:
    """Build a ClickException with optional suggestions."""
    return click.ClickException(
        format_cli_message(message, suggestions=suggestions, see_help=see_help)
    )


def usage_error(
    message: str,
    *,
    suggestions: Sequence[str] = (),
    see_help: str | None = None,
) -> click.UsageError:
    """Build a UsageError with optional suggestions."""
    return click.UsageError(format_cli_message(message, suggestions=suggestions, see_help=see_help))


def alpha_error_to_click_exception(
    exc: AlphaXivError,
    *,
    suggestions: Sequence[str] = (),
    see_help: str | None = None,
) -> click.ClickException:
    """Convert an alphaXiv SDK exception into a Click-friendly error."""
    derived_suggestions = list(suggestions)
    derived_help = see_help
    if isinstance(exc, AuthRequiredError):
        derived_suggestions = list(derived_suggestions) + list(AUTH_TRY_COMMANDS)
        derived_help = AUTH_HELP_PATH
    return click_error(str(exc), suggestions=derived_suggestions, see_help=derived_help)
