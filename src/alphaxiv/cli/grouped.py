"""Grouped Click help output."""

from __future__ import annotations

from difflib import get_close_matches
from inspect import cleandoc

import click
from click.parser import _split_opt

from .messages import format_cli_message

UNKNOWN_COMMAND_FALLBACKS: dict[str, dict[str, tuple[str, ...]]] = {
    "alphaxiv": {
        "status": ("alphaxiv context show", "alphaxiv auth status"),
        "clear": ("alphaxiv context clear", "alphaxiv auth clear"),
        "overview": ("alphaxiv paper overview <paper-id>",),
        "overview-status": ("alphaxiv paper overview-status <paper-id>",),
        "resources": ("alphaxiv paper resources <paper-id>",),
        "pdf": (
            "alphaxiv paper pdf url <paper-id>",
            "alphaxiv paper pdf download <paper-id> ./paper.pdf",
        ),
        "comments": ("alphaxiv paper comments list <paper-id>",),
        "search-papers": ('alphaxiv search papers "<query>"',),
        "search-topics": ('alphaxiv search topics "<query>"',),
        "search-organizations": ('alphaxiv search organizations "<query>"',),
    },
    "alphaxiv paper": {
        "full-text": ("alphaxiv paper text <paper-id>",),
        "fulltext": ("alphaxiv paper text <paper-id>",),
        "pdf-text": ("alphaxiv paper text <paper-id>",),
        "download-pdf": ("alphaxiv paper pdf download <paper-id> ./paper.pdf",),
    },
    "alphaxiv assistant": {
        "use": ("alphaxiv context use assistant <session-id>",),
        "clear": ("alphaxiv context clear assistant",),
        "models": ("alphaxiv assistant model",),
    },
}


def _canonical_command_path(ctx: click.Context) -> str:
    parts = ctx.command_path.split()
    if not parts:
        return "alphaxiv"
    if len(parts) == 1:
        return "alphaxiv"
    return " ".join(["alphaxiv", *parts[1:]])


class WrappedHelpGroup(click.Group):
    """Click group that wraps command help instead of truncating it."""

    def _command_help(self, cmd: click.Command) -> str:
        if cmd.short_help:
            return cmd.short_help.strip()
        if not cmd.help:
            return ""
        return " ".join(cleandoc(cmd.help).split())

    def format_commands(self, ctx, formatter):
        rows = []
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is not None and not cmd.hidden:
                rows.append((name, self._command_help(cmd)))
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)

    def _unknown_command_suggestions(self, ctx: click.Context, token: str) -> list[str]:
        command_path = _canonical_command_path(ctx)
        visible_commands = [
            name
            for name in self.list_commands(ctx)
            if (cmd := self.get_command(ctx, name)) is not None and not cmd.hidden
        ]
        suggestions: list[str] = []
        normalized_token = token.strip().lower()

        close_match = get_close_matches(normalized_token, visible_commands, n=1, cutoff=0.6)
        if close_match:
            suggestions.append(f"{command_path} {close_match[0]}")

        suggestions.extend(
            UNKNOWN_COMMAND_FALLBACKS.get(command_path, {}).get(normalized_token, ())
        )

        if command_path == "alphaxiv paper" and not suggestions:
            if "text" in normalized_token or "full" in normalized_token:
                suggestions.append("alphaxiv paper text <paper-id>")
            if "pdf" in normalized_token and "download" in normalized_token:
                suggestions.append("alphaxiv paper pdf download <paper-id> ./paper.pdf")
        if command_path == "alphaxiv assistant" and not suggestions:
            if "chat" in normalized_token or "ask" in normalized_token:
                suggestions.append('alphaxiv assistant start "<message>"')
            if "message" in normalized_token or "history" in normalized_token:
                suggestions.append("alphaxiv assistant history")
        if command_path == "alphaxiv feed" and not suggestions:
            if "filter" in normalized_token or "topic" in normalized_token:
                suggestions.append('alphaxiv feed filters search "<query>"')
            if "recent" in normalized_token or "rank" in normalized_token:
                suggestions.append("alphaxiv feed list --sort hot")

        unique: list[str] = []
        seen: set[str] = set()
        for item in suggestions:
            cleaned = item.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            unique.append(cleaned)
        return unique

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        cmd_name = click.utils.make_str(args[0])
        original_cmd_name = cmd_name

        cmd = self.get_command(ctx, cmd_name)
        if cmd is None and ctx.token_normalize_func is not None:
            cmd_name = ctx.token_normalize_func(cmd_name)
            cmd = self.get_command(ctx, cmd_name)

        if cmd is None and not ctx.resilient_parsing:
            if _split_opt(cmd_name)[0]:
                self.parse_args(ctx, args)
            suggestions = self._unknown_command_suggestions(ctx, original_cmd_name)
            raise click.UsageError(
                format_cli_message(
                    f"No such command '{original_cmd_name}'.",
                    suggestions=suggestions,
                    see_help=f"{_canonical_command_path(ctx)} --help",
                )
            )
        return cmd_name if cmd else None, cmd, args[1:]
