"""Grouped Click help output."""

from __future__ import annotations

from collections import OrderedDict

import click


class SectionedGroup(click.Group):
    """Click group that renders commands in logical sections."""

    command_sections = OrderedDict(
        [
            ("Session", ["login", "logout", "use", "status", "clear"]),
            (
                "Research",
                [
                    "search",
                    "search-papers",
                    "search-organizations",
                    "search-topics",
                    "overview",
                    "overview-status",
                    "resources",
                ],
            ),
        ]
    )
    command_groups = OrderedDict([("Command Groups", ["assistant", "feed", "paper", "pdf"])])

    def format_commands(self, ctx, formatter):
        commands = {name: self.get_command(ctx, name) for name in self.list_commands(ctx)}

        for section, names in self.command_sections.items():
            rows = []
            for name in names:
                cmd = commands.get(name)
                if cmd is not None and not cmd.hidden:
                    rows.append((name, cmd.get_short_help_str(limit=formatter.width)))
            if rows:
                with formatter.section(section):
                    formatter.write_dl(rows)

        for section, names in self.command_groups.items():
            rows = []
            for name in names:
                cmd = commands.get(name)
                if isinstance(cmd, click.Group):
                    rows.append((name, ", ".join(sorted(cmd.list_commands(ctx)))))
            if rows:
                with formatter.section(section):
                    formatter.write_dl(rows)
