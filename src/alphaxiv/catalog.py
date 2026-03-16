"""Shared workflow and integration metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GuideEntry:
    """Workflow guide content rendered by the CLI."""

    name: str
    title: str
    summary: str
    body: str


@dataclass(frozen=True, slots=True)
class IntegrationTarget:
    """Agent integration metadata and install locations."""

    key: str
    label: str
    kind: str
    description: str
    repo_source: Path
    package_source: Path
    user_relative_path: Path
    project_relative_path: Path
    guidance: str
    primary_relative_path: Path


GUIDE_ENTRIES: dict[str, GuideEntry] = {
    "research": GuideEntry(
        name="research",
        title="Research Workflow",
        summary="Find recent important papers, inspect them, then synthesize with the assistant.",
        body=(
            "Goal\n"
            "  Discover recent important papers for a topic, reduce them to a shortlist, then use\n"
            "  the assistant only after deterministic retrieval.\n\n"
            "Recommended sequence\n"
            '  1. Discover topic slugs with `alphaxiv feed filters search "<topic>"`.\n'
            '  2. Search directly with `alphaxiv search papers "<topic>"` when you already have keywords.\n'
            "  3. Pull ranked candidates with `alphaxiv feed list --interval 90-days --sort hot` and\n"
            "     source-specific passes like `--source github --sort most-stars`.\n"
            "  4. Inspect candidates with `alphaxiv paper show`, `paper abstract`, `paper summary`,\n"
            "     `paper resources`, and `paper similar`.\n"
            "  5. Use `alphaxiv assistant start` after the shortlist exists, not as the first search step.\n\n"
            "How to interpret the outputs\n"
            "  - `search` is keyword-driven lookup.\n"
            "  - `feed` is recent or ranked discovery and is usually better for questions like\n"
            '    "what matters from the last 3 months?"\n'
            "  - `paper summary` is the fast AI digest; `paper overview` is the longer generated write-up.\n\n"
            "Common mistakes\n"
            "  - Using `assistant` before you have deterministic candidates.\n"
            "  - Using `search` when you really need recency/ranking.\n"
            "  - Asking for the PDF file when you actually want extracted text; use `paper text` for that."
        ),
    ),
    "paper": GuideEntry(
        name="paper",
        title="Paper Inspection Guide",
        summary="Choose the right paper command for metadata, summaries, text, PDFs, and related resources.",
        body=(
            "Goal\n"
            "  Inspect one paper with the right command instead of guessing between similar-looking outputs.\n\n"
            "Use the commands this way\n"
            "  - `alphaxiv paper show`: ids, authors, topics, and core links.\n"
            "  - `alphaxiv paper abstract`: the author-written abstract.\n"
            "  - `alphaxiv paper summary`: the short structured AI digest.\n"
            "  - `alphaxiv paper overview`: the long AI write-up.\n"
            "  - `alphaxiv paper text`: readable text extracted from the PDF.\n"
            "  - `alphaxiv paper pdf url` / `paper pdf download`: the actual PDF file.\n"
            "  - `alphaxiv paper resources`: citations, transcript, implementations, mentions, and links.\n"
            "  - `alphaxiv paper similar`: nearby papers worth checking next.\n\n"
            "When to save context\n"
            "  If several commands target the same paper, run `alphaxiv context use paper <paper-id>` first\n"
            "  so later paper commands can omit the id.\n\n"
            "Common mistakes\n"
            "  - Confusing `summary` with `overview`.\n"
            "  - Confusing `text` with `pdf download`.\n"
            "  - Forgetting that optional `[paper-id]` commands use the saved current paper context."
        ),
    ),
    "assistant": GuideEntry(
        name="assistant",
        title="Assistant Guide",
        summary="Use the assistant after retrieval for synthesis, follow-up questions, and paper-grounded chats.",
        body=(
            "Goal\n"
            "  Use the authenticated alphaXiv assistant as a synthesis layer after you have already retrieved\n"
            "  papers through `search`, `feed`, or `paper`.\n\n"
            "Recommended sequence\n"
            '  1. Start a new chat with `alphaxiv assistant start "<message>"`.\n'
            "  2. Add `--paper <paper-id>` when the new chat should be grounded in one paper.\n"
            '  3. Continue a chat with `alphaxiv assistant reply "<message>"`.\n'
            "  4. Inspect or recover sessions with `assistant list` and `assistant history`.\n"
            "  5. Save a session with `alphaxiv context use assistant <session-id>` when you want replies\n"
            "     to default to that chat later.\n\n"
            "What the assistant is best at\n"
            "  - comparing shortlisted papers\n"
            "  - summarizing differences or reading order\n"
            "  - answering follow-up questions about one paper\n"
            "  - broad research synthesis after deterministic retrieval\n\n"
            "Common mistakes\n"
            "  - Treating `assistant` as the first-step search surface.\n"
            "  - Assuming a saved paper context automatically grounds `assistant start`; it does not.\n"
            "  - Using `start` when you meant to continue an existing chat with `reply`."
        ),
    ),
    "feed": GuideEntry(
        name="feed",
        title="Feed Guide",
        summary="Discover live topic filters, then rank recent papers by hotness, likes, or source traction.",
        body=(
            "Goal\n"
            "  Use the public alphaXiv homepage feed for recent or ranked discovery.\n\n"
            "Recommended sequence\n"
            "  1. Run `alphaxiv feed filters` to inspect the current filter groups.\n"
            '  2. Run `alphaxiv feed filters search "<query>"` to find live topic slugs and organizations.\n'
            "  3. Use those values with `alphaxiv feed list`.\n"
            "  4. Compare `--sort hot`, `--sort likes`, and `--source github --sort most-stars`\n"
            "     to combine visibility, engagement, and implementation traction.\n\n"
            "How to interpret the ranking modes\n"
            "  - `hot`: the homepage’s main importance-style feed.\n"
            "  - `likes`: papers with the most visible engagement.\n"
            "  - `most-stars` with `--source github`: papers with strong code traction.\n\n"
            "Common mistakes\n"
            "  - Using natural-language topic words directly in `feed list` instead of discovering the\n"
            "    accepted `--topic` value with `feed filters search`.\n"
            "  - Using `search` when you actually need recency or ranking.\n"
            "  - Treating one ranking alone as the full answer to what is important."
        ),
    ),
}


INTEGRATION_TARGETS: dict[str, IntegrationTarget] = {
    "codex": IntegrationTarget(
        key="codex",
        label="Codex",
        kind="directory",
        description="Install the alphaXiv Codex skill tree so Codex can discover research workflows.",
        repo_source=Path("skills") / "alphaxiv",
        package_source=Path("data") / "skills" / "alphaxiv",
        user_relative_path=Path(".codex") / "skills" / "alphaxiv",
        project_relative_path=Path("skills") / "alphaxiv",
        primary_relative_path=Path("SKILL.md"),
        guidance=(
            "Codex integration installs the full alphaXiv skill directory.\n\n"
            "User scope:\n"
            "  $CODEX_HOME/skills/alphaxiv or ~/.codex/skills/alphaxiv\n\n"
            "Project scope:\n"
            "  ./skills/alphaxiv\n\n"
            "Installed files include the main `SKILL.md`, `agents/openai.yaml`, and the reference\n"
            "workflow files used for command selection and research guidance."
        ),
    ),
    "claude-code": IntegrationTarget(
        key="claude-code",
        label="Claude Code",
        kind="file",
        description="Install a reusable alphaXiv research subagent for Claude Code.",
        repo_source=Path("integrations") / "claude-code" / "alphaxiv-research.md",
        package_source=Path("data") / "integrations" / "claude-code" / "alphaxiv-research.md",
        user_relative_path=Path(".claude") / "agents" / "alphaxiv-research.md",
        project_relative_path=Path(".claude") / "agents" / "alphaxiv-research.md",
        primary_relative_path=Path("alphaxiv-research.md"),
        guidance=(
            "Claude Code integration installs a Markdown subagent with YAML frontmatter.\n\n"
            "User scope:\n"
            "  ~/.claude/agents/alphaxiv-research.md\n\n"
            "Project scope:\n"
            "  ./.claude/agents/alphaxiv-research.md\n\n"
            "The subagent is meant for alphaXiv CLI research tasks and prefers deterministic retrieval\n"
            "with `search`, `feed`, and `paper` before using `assistant`."
        ),
    ),
    "opencode": IntegrationTarget(
        key="opencode",
        label="OpenCode",
        kind="directory",
        description="Install a small namespaced OpenCode command pack for alphaXiv research workflows.",
        repo_source=Path("integrations") / "opencode" / "commands" / "alphaxiv",
        package_source=Path("data") / "integrations" / "opencode" / "commands" / "alphaxiv",
        user_relative_path=Path(".config") / "opencode" / "commands" / "alphaxiv",
        project_relative_path=Path(".opencode") / "commands" / "alphaxiv",
        primary_relative_path=Path("research.md"),
        guidance=(
            "OpenCode integration installs a namespaced Markdown command pack.\n\n"
            "User scope:\n"
            "  ~/.config/opencode/commands/alphaxiv/\n\n"
            "Project scope:\n"
            "  ./.opencode/commands/alphaxiv/\n\n"
            "Installed commands are focused on research workflows such as recent-paper discovery,\n"
            "paper inspection, feed usage, and assistant follow-up."
        ),
    ),
}
