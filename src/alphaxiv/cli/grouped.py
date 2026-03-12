"""Grouped Click help output."""

from __future__ import annotations

from inspect import cleandoc

import click


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
