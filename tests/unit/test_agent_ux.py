from __future__ import annotations

import importlib
from datetime import UTC, datetime
from pathlib import Path

from click.testing import CliRunner

from alphaxiv.alphaxiv_cli import cli
from alphaxiv.cli.helpers import save_assistant_context, save_context
from alphaxiv.types import (
    AssistantContext,
    AssistantMessage,
    FeedFilterSearchResults,
    HomepageSearchResults,
    OrganizationResult,
    OverviewSummary,
    PaperOverview,
    ResolvedPaper,
    SearchResult,
)

agent_assets = importlib.import_module("alphaxiv.agent_assets")
assistant_cli = importlib.import_module("alphaxiv.cli.assistant")
context_cli = importlib.import_module("alphaxiv.cli.session")
explore_cli = importlib.import_module("alphaxiv.cli.explore")
folders_cli = importlib.import_module("alphaxiv.cli.folders")
paper_cli = importlib.import_module("alphaxiv.cli.paper")


def _resolved(identifier: str) -> ResolvedPaper:
    return ResolvedPaper(
        input_id=identifier,
        versionless_id="1706.03762",
        canonical_id="1706.03762v7",
        version_id="0189b531-a930-7613-9d2e-dd918c8435a5",
        group_id="015c9ef4-ac30-768d-928b-847320902575",
        title="Attention Is All You Need",
    )


def test_guide_root_and_research_output() -> None:
    runner = CliRunner()

    root = runner.invoke(cli, ["guide"])
    research = runner.invoke(cli, ["guide", "research"])

    assert root.exit_code == 0
    assert "alphaXiv Workflow Guides" in root.output
    assert "research" in root.output
    assert research.exit_code == 0
    assert "Research Workflow" in research.output
    assert "feed filters search" in research.output
    assert "assistant" in research.output


def test_context_show_json(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_context(_resolved("1706.03762"))
    save_assistant_context(
        AssistantContext(
            session_id="session-existing",
            variant="homepage",
            paper=None,
            newest_message_at=datetime(2026, 3, 16, 9, 0, tzinfo=UTC),
            title="Earlier chat",
        )
    )

    result = runner.invoke(cli, ["context", "show", "--json"])

    assert result.exit_code == 0
    assert '"paper"' in result.output
    assert '"assistant"' in result.output
    assert '"preferred_id": "1706.03762v7"' in result.output
    assert '"session_id": "session-existing"' in result.output


def test_search_and_feed_json(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        explore_cli,
        "fetch_homepage_search",
        lambda _query: HomepageSearchResults(
            query="transformers",
            papers=[
                SearchResult(
                    link="/abs/1706.03762",
                    paper_id="1706.03762",
                    title="Attention Is All You Need",
                    snippet="Transformers",
                    raw={},
                )
            ],
            organizations=[],
            topics=["transformers"],
            raw={},
        ),
    )
    monkeypatch.setattr(
        explore_cli,
        "fetch_feed_filter_search",
        lambda _query: FeedFilterSearchResults(
            query="agentic",
            topics=["agents"],
            organizations=[
                OrganizationResult(id="org-meta", name="Meta", image=None, slug="meta", raw={})
            ],
            raw={},
        ),
    )

    search_result = runner.invoke(cli, ["search", "all", "transformers", "--json"])
    filter_result = runner.invoke(cli, ["feed", "filters", "search", "agentic", "--json"])

    assert search_result.exit_code == 0
    assert '"query": "transformers"' in search_result.output
    assert '"paper_id": "1706.03762"' in search_result.output
    assert filter_result.exit_code == 0
    assert '"topics": [' in filter_result.output
    assert '"agents"' in filter_result.output
    assert '"slug": "meta"' in filter_result.output


def test_paper_summary_json_and_raw_conflict(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        paper_cli,
        "fetch_overview",
        lambda _identifier, language="en": PaperOverview(
            version_id="version-1",
            language=language,
            title="Attention Is All You Need",
            abstract="Original abstract",
            summary=OverviewSummary(
                summary="Short AI digest",
                original_problem=["slow sequence models"],
                solution=["transformer"],
                key_insights=["self-attention"],
                results=["state of the art"],
                raw={"summary": "Short AI digest"},
            ),
            overview_markdown="## Overview",
            intermediate_report=None,
            citations=[],
            raw={},
        ),
    )

    json_result = runner.invoke(cli, ["paper", "summary", "1706.03762", "--json"])
    conflict_result = runner.invoke(cli, ["paper", "summary", "1706.03762", "--raw", "--json"])

    assert json_result.exit_code == 0
    assert '"requested_id": "1706.03762"' in json_result.output
    assert '"summary": "Short AI digest"' in json_result.output
    assert conflict_result.exit_code != 0
    assert "Use either --raw or --json, not both." in conflict_result.output


def test_folders_list_json_and_conflict(monkeypatch) -> None:
    runner = CliRunner()
    folder = folders_cli.Folder(
        id="folder-1",
        name="Want to read",
        folder_type="custom",
        order=1,
        parent_id=None,
        sharing_status="private",
        papers=[],
        raw={"id": "folder-1"},
    )
    monkeypatch.setattr(folders_cli, "fetch_folders", lambda: [folder])

    json_result = runner.invoke(cli, ["folders", "list", "--json"])
    conflict_result = runner.invoke(cli, ["folders", "list", "--raw", "--json"])

    assert json_result.exit_code == 0
    assert '"folders": [' in json_result.output
    assert '"name": "Want to read"' in json_result.output
    assert conflict_result.exit_code != 0
    assert "Use either --raw or --json, not both." in conflict_result.output


def test_assistant_history_json_and_conflict(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_assistant_context(
        AssistantContext(
            session_id="session-existing",
            variant="homepage",
            paper=None,
            newest_message_at=None,
            title="Earlier chat",
        )
    )
    monkeypatch.setattr(
        assistant_cli,
        "fetch_history",
        lambda _session_id: [
            AssistantMessage(
                id="message-1",
                message_type="output_text",
                parent_message_id=None,
                selected_at=None,
                tool_use_id=None,
                kind=None,
                content="Helios is a video model.",
                model="claude-4.6-sonnet",
                feedback_type=None,
                feedback_category=None,
                feedback_details=None,
                raw={"type": "output_text"},
            )
        ],
    )

    json_result = runner.invoke(cli, ["assistant", "history", "--json"])
    conflict_result = runner.invoke(cli, ["assistant", "history", "--raw", "--json"])

    assert json_result.exit_code == 0
    assert '"session_id": "session-existing"' in json_result.output
    assert '"type": "output_text"' in json_result.output
    assert conflict_result.exit_code != 0
    assert "Use either --raw or --json, not both." in conflict_result.output


def test_skill_install_status_show_and_uninstall(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    home = tmp_path / "home"
    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.setattr(agent_assets.Path, "home", lambda: home)
    monkeypatch.setattr(agent_assets.Path, "cwd", lambda: tmp_path / "project")

    install = runner.invoke(cli, ["skill", "install"])
    status = runner.invoke(cli, ["skill", "status", "--scope", "all", "--json"])
    show = runner.invoke(cli, ["skill", "show", "--target", "codex"])

    assert install.exit_code == 0
    assert "Installed" in install.output
    assert (codex_home / "skills" / "alphaxiv" / "SKILL.md").exists()
    assert (home / ".claude" / "agents" / "alphaxiv-research.md").exists()
    assert (home / ".config" / "opencode" / "commands" / "alphaxiv" / "research.md").exists()

    assert status.exit_code == 0
    assert '"target": "codex"' in status.output
    assert '"installed": true' in status.output
    assert show.exit_code == 0
    assert "# SKILL.md" in show.output
    assert "alphaXiv CLI" in show.output

    uninstall = runner.invoke(cli, ["skill", "uninstall", "--yes"])
    assert uninstall.exit_code == 0
    assert "Removed" in uninstall.output
    assert not (codex_home / "skills" / "alphaxiv" / "SKILL.md").exists()


def test_agent_show_and_codex_skill_source_match() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["agent", "show", "codex"])

    assert result.exit_code == 0
    assert "Codex Install Paths" in result.output
    assert "SKILL.md" in result.output

    bundle = agent_assets.get_source_bundle("codex")
    repo_skill = Path("skills/alphaxiv/SKILL.md").read_text(encoding="utf-8")
    assert bundle[Path("SKILL.md")] == repo_skill
