from __future__ import annotations

import importlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from click.testing import CliRunner

from alphaxiv.alphaxiv_cli import cli
from alphaxiv.types import (
    CommentAuthor,
    ExploreFilterOptions,
    FeedCard,
    FeedFilterSearchResults,
    Folder,
    FolderPaper,
    HomepageSearchResults,
    OrganizationResult,
    PaperComment,
    ResolvedPaper,
    SearchResult,
    UrlMetadata,
)

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


def test_top_level_help_shows_only_groups() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Commands:" in result.output
    assert "auth" in result.output
    assert "context" in result.output
    assert "search" in result.output
    assert "feed" in result.output
    assert "paper" in result.output
    assert "assistant" in result.output
    assert "folders" in result.output
    assert "\n  comments  " not in result.output
    assert "\n  status" not in result.output
    assert "clear   Clear the saved paper context" not in result.output
    assert "search-papers" not in result.output
    assert "pdf        " not in result.output


def test_group_help_wraps_without_ellipsis() -> None:
    runner = CliRunner()

    paper_help = runner.invoke(cli, ["paper", "--help"])
    assistant_help = runner.invoke(cli, ["assistant", "--help"])
    search_help = runner.invoke(cli, ["search", "--help"])
    comment_help = runner.invoke(cli, ["paper", "comments", "--help"])

    assert paper_help.exit_code == 0
    assert assistant_help.exit_code == 0
    assert search_help.exit_code == 0
    assert comment_help.exit_code == 0
    assert "readable text extracted from the paper PDF" in paper_help.output
    assert "grounded in one paper" in assistant_help.output
    assert "Use `feed` when you want recent" in search_help.output
    assert "comment actions" in comment_help.output


def test_removed_commands_fail_cleanly() -> None:
    runner = CliRunner()
    removed_commands = [
        ["status"],
        ["clear"],
        ["search-papers", "helios"],
        ["search-organizations", "mit"],
        ["search-topics", "reinforcement learning"],
        ["overview", "1706.03762"],
        ["overview-status", "1706.03762"],
        ["resources", "1706.03762"],
        ["pdf", "url", "1706.03762"],
        ["assistant", "use", "session-existing"],
        ["assistant", "clear"],
        ["comments", "upvote", "comment-root"],
        ["paper", "use", "1706.03762"],
        ["paper", "comments", "1706.03762"],
    ]

    for command in removed_commands:
        result = runner.invoke(cli, command)
        assert result.exit_code != 0
        assert "No such command" in result.output


def test_unknown_commands_show_replacement_suggestions() -> None:
    runner = CliRunner()

    removed_root = runner.invoke(cli, ["overview", "1706.03762"])
    semantic_paper = runner.invoke(cli, ["paper", "full-text", "1706.03762"])
    removed_assistant = runner.invoke(cli, ["assistant", "models"])

    assert removed_root.exit_code != 0
    assert "alphaxiv paper overview <paper-id>" in removed_root.output
    assert "See: alphaxiv --help" in removed_root.output

    assert semantic_paper.exit_code != 0
    assert "alphaxiv paper text <paper-id>" in semantic_paper.output
    assert "See: alphaxiv paper --help" in semantic_paper.output

    assert removed_assistant.exit_code != 0
    assert "alphaxiv assistant model" in removed_assistant.output
    assert "See: alphaxiv assistant --help" in removed_assistant.output


def test_search_all_shows_topics_and_organizations(monkeypatch) -> None:
    runner = CliRunner()
    results = HomepageSearchResults(
        query="reinforcement learning",
        papers=[],
        organizations=[
            OrganizationResult(id="org-mit", name="MIT", image=None, slug="mit", raw={})
        ],
        topics=["deep-reinforcement-learning"],
        raw={},
    )
    monkeypatch.setattr(explore_cli, "fetch_homepage_search", lambda _query: results)

    result = runner.invoke(cli, ["search", "all", "reinforcement learning"])
    assert result.exit_code == 0
    assert "Suggested Topics" in result.output
    assert "deep-reinforcement-learning" in result.output
    assert "MIT" in result.output


def test_search_papers_command(monkeypatch) -> None:
    runner = CliRunner()
    results = [
        SearchResult(
            link="/abs/2603.04379",
            paper_id="2603.04379",
            title="Helios",
            snippet="Fast video generation",
            raw={},
        )
    ]
    monkeypatch.setattr(explore_cli, "fetch_paper_search", lambda _query: results)

    result = runner.invoke(cli, ["search", "papers", "helios"])
    assert result.exit_code == 0
    assert "Paper Search Results for: helios" in result.output
    assert "2603.04379" in result.output


def test_search_organizations_command(monkeypatch) -> None:
    runner = CliRunner()
    organizations = [OrganizationResult(id="org-mit", name="MIT", image=None, slug="mit", raw={})]
    monkeypatch.setattr(explore_cli, "fetch_organization_search", lambda _query: organizations)

    result = runner.invoke(cli, ["search", "organizations", "mit"])
    assert result.exit_code == 0
    assert "MIT" in result.output
    assert "mit" in result.output


def test_search_topics_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        explore_cli, "fetch_topic_search", lambda _query: ["deep-reinforcement-learning"]
    )

    result = runner.invoke(cli, ["search", "topics", "reinforcement learning"])
    assert result.exit_code == 0
    assert "Suggested Topics" in result.output
    assert "deep-reinforcement-learning" in result.output


def test_feed_list_renders_cards(monkeypatch) -> None:
    runner = CliRunner()
    cards = [
        FeedCard(
            group_id="group-helios",
            paper_id="2603.04379",
            canonical_id="2603.04379v1",
            version_id="version-helios",
            title="Helios",
            abstract="We introduce Helios.",
            summary="Helios summary",
            result_highlights=["19.53 FPS"],
            publication_date=None,
            updated_at=None,
            topics=["computer-science", "generative-models"],
            organizations=[],
            authors=["Shenghai Yuan"],
            image_url=None,
            upvotes=107,
            total_votes=39,
            x_likes=0,
            visits=2974,
            visits_last_7_days=2974,
            github_stars=235,
            github_url="https://github.com/PKU-YuanGroup/Helios",
            raw={},
        )
    ]
    monkeypatch.setattr(explore_cli, "fetch_feed_cards", lambda **_kwargs: cards)

    result = runner.invoke(cli, ["feed", "list", "--sort", "hot", "--limit", "1"])
    assert result.exit_code == 0
    assert "alphaXiv Feed" in result.output
    assert "2603.04379" in result.output
    assert "107" in result.output


def test_feed_filters_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        explore_cli,
        "fetch_filter_options",
        lambda: ExploreFilterOptions(
            sorts=["Hot", "Likes", "GitHub", "Twitter (X)"],
            menu_categories=["Computer Science"],
            intervals=["7 Days", "All time"],
            sources=["GitHub", "Twitter (X)"],
            organizations=[
                OrganizationResult(id="org-mit", name="MIT", image=None, slug="mit", raw={})
            ],
            raw={},
        ),
    )

    result = runner.invoke(cli, ["feed", "filters"])
    assert result.exit_code == 0
    assert "Feed Sorts" in result.output
    assert "Feed Sources" in result.output
    assert "MIT" in result.output


def test_feed_filters_search_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        explore_cli,
        "fetch_feed_filter_search",
        lambda _query: FeedFilterSearchResults(
            query="agentic",
            topics=["agentic-frameworks", "agents"],
            organizations=[
                OrganizationResult(id="org-meta", name="Meta", image=None, slug="meta", raw={})
            ],
            raw={},
        ),
    )

    result = runner.invoke(cli, ["feed", "filters", "search", "agentic"])
    assert result.exit_code == 0
    assert "Feed Filter Topics for: agentic" in result.output
    assert "agentic-frameworks" in result.output
    assert "--topic" in result.output
    assert "Meta" in result.output


def _comment_fixture() -> list[PaperComment]:
    return [
        PaperComment(
            id="comment-root",
            paper_group_id="015c9ef4-ac30-768d-928b-847320902575",
            paper_version_id="0189b531-a930-7613-9d2e-dd918c8435a5",
            parent_comment_id=None,
            title="Interesting compression result",
            body="How does this compare at longer horizons?",
            tag="question",
            annotation=None,
            upvotes=12,
            has_upvoted=False,
            has_downvoted=False,
            has_flagged=False,
            is_author=False,
            was_edited=False,
            universal_id="1706.03762",
            paper_title="Attention Is All You Need",
            author_responded=True,
            date=datetime(2026, 3, 10, 10, 11, 12, tzinfo=UTC),
            author=CommentAuthor(
                id="author-1",
                username="research_reader",
                real_name="Research Reader",
                avatar_url=None,
                institution="MIT",
                reputation=42,
                verified=True,
                role="user",
                raw={},
            ),
            endorsements=[],
            responses=[],
            raw={"id": "comment-root"},
        )
    ]


def test_paper_comments_list_uses_current_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    monkeypatch.setattr(context_cli, "resolve_paper_identifier", lambda _: _resolved("1706.03762"))
    runner.invoke(cli, ["context", "use", "paper", "1706.03762"])

    monkeypatch.setattr(paper_cli, "fetch_comments", lambda _identifier: _comment_fixture())

    result = runner.invoke(cli, ["paper", "comments", "list"])

    assert result.exit_code == 0
    assert "Comments for 1706.03762v7" in result.output
    assert "Research Reader" in result.output
    assert "Interesting compression result" in result.output


def test_paper_comments_add_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        paper_cli,
        "create_comment",
        lambda _identifier, **_kwargs: _comment_fixture()[0],
    )

    result = runner.invoke(
        cli,
        [
            "paper",
            "comments",
            "add",
            "1706.03762v7",
            "--body",
            "Helpful note",
            "--title",
            "Useful note",
            "--tag",
            "general",
        ],
    )

    assert result.exit_code == 0
    assert "Created comment" in result.output
    assert "comment-root" in result.output


def test_paper_comments_reply_command(monkeypatch) -> None:
    runner = CliRunner()
    reply = replace(_comment_fixture()[0], id="comment-child", parent_comment_id="comment-root")
    monkeypatch.setattr(
        paper_cli,
        "reply_to_comment",
        lambda _identifier, _comment_id, **_kwargs: reply,
    )

    result = runner.invoke(
        cli,
        [
            "paper",
            "comments",
            "reply",
            "1706.03762v7",
            "comment-root",
            "--body",
            "Helpful reply",
            "--tag",
            "research",
        ],
    )

    assert result.exit_code == 0
    assert "Created reply" in result.output
    assert "comment-child" in result.output


def test_paper_comments_upvote_requires_confirmation(monkeypatch) -> None:
    runner = CliRunner()
    called = False

    def _toggle(_comment_id: str):
        nonlocal called
        called = True
        return {"ok": True}

    monkeypatch.setattr(paper_cli, "toggle_comment_upvote", _toggle)

    result = runner.invoke(cli, ["paper", "comments", "upvote", "comment-root"], input="n\n")

    assert result.exit_code != 0
    assert called is False


def test_paper_comments_delete_command(monkeypatch) -> None:
    runner = CliRunner()
    deleted: list[str] = []

    monkeypatch.setattr(paper_cli, "delete_comment", lambda comment_id: deleted.append(comment_id))

    result = runner.invoke(cli, ["paper", "comments", "delete", "comment-root", "--yes"])

    assert result.exit_code == 0
    assert deleted == ["comment-root"]
    assert "Deleted comment" in result.output


def test_paper_comments_delete_requires_confirmation(monkeypatch) -> None:
    runner = CliRunner()
    called = False

    def _delete(_comment_id: str) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(paper_cli, "delete_comment", _delete)

    result = runner.invoke(cli, ["paper", "comments", "delete", "comment-root"], input="n\n")

    assert result.exit_code != 0
    assert called is False


def test_paper_similar_command(monkeypatch) -> None:
    runner = CliRunner()
    cards = [
        FeedCard(
            group_id="group-helios",
            paper_id="2603.04379",
            canonical_id="2603.04379v1",
            version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
            title="Helios",
            abstract="We introduce Helios.",
            summary="Helios summary",
            result_highlights=[],
            publication_date=None,
            updated_at=None,
            topics=["Computer Science", "cs.CV"],
            organizations=[],
            authors=["Shenghai Yuan"],
            image_url=None,
            upvotes=107,
            total_votes=39,
            x_likes=0,
            visits=2974,
            visits_last_7_days=2974,
            github_stars=235,
            github_url="https://github.com/PKU-YuanGroup/Helios",
            raw={},
        ),
        FeedCard(
            group_id="group-rlm",
            paper_id="2512.24601",
            canonical_id="2512.24601v1",
            version_id="version-rlm",
            title="Recursive Language Models",
            abstract="A new model family.",
            summary="RLM summary",
            result_highlights=[],
            publication_date=None,
            updated_at=None,
            topics=["Computer Science"],
            organizations=[],
            authors=["Andrew McCallum"],
            image_url=None,
            upvotes=514,
            total_votes=188,
            x_likes=325,
            visits=1200,
            visits_last_7_days=800,
            github_stars=165,
            github_url="https://github.com/example/rlm",
            raw={},
        ),
    ]
    monkeypatch.setattr(
        paper_cli,
        "fetch_similar",
        lambda _identifier, limit=None: cards[:limit] if limit is not None else cards,
    )

    result = runner.invoke(cli, ["paper", "similar", "2603.04379v1", "--limit", "1"])

    assert result.exit_code == 0
    assert "Helios" in result.output
    assert "Recursive Language Models" not in result.output


def test_paper_vote_requires_confirmation(monkeypatch) -> None:
    runner = CliRunner()
    called = False

    def _toggle(_identifier: str):
        nonlocal called
        called = True
        return {"ok": True}

    monkeypatch.setattr(paper_cli, "toggle_vote", _toggle)

    result = runner.invoke(cli, ["paper", "vote", "2603.04379v1"], input="n\n")

    assert result.exit_code != 0
    assert called is False


def test_paper_view_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(paper_cli, "record_view", lambda _identifier: {"ok": True})

    result = runner.invoke(cli, ["paper", "view", "2603.04379v1", "--yes"])

    assert result.exit_code == 0
    assert "Recorded paper view" in result.output


def test_paper_pdf_commands(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        paper_cli,
        "fetch_pdf_url",
        lambda _identifier: "https://fetcher.alphaxiv.org/v2/pdf/1706.03762v7.pdf",
    )
    output_path = tmp_path / "attention.pdf"
    monkeypatch.setattr(
        paper_cli, "fetch_pdf_download", lambda _identifier, _path: Path(output_path)
    )

    url_result = runner.invoke(cli, ["paper", "pdf", "url", "1706.03762"])
    download_result = runner.invoke(
        cli,
        ["paper", "pdf", "download", "1706.03762", str(output_path)],
    )

    assert url_result.exit_code == 0
    assert "fetcher.alphaxiv.org" in url_result.output
    assert download_result.exit_code == 0
    assert "Downloaded PDF to" in download_result.output
    assert output_path.name in download_result.output


def test_paper_pdf_download_usage_error_shows_examples() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["paper", "pdf", "download"])

    assert result.exit_code != 0
    assert "Expected either <path> or <paper-id> <path>." in result.output
    assert "alphaxiv paper pdf download ./paper.pdf" in result.output
    assert "alphaxiv paper pdf download 1706.03762 ./paper.pdf" in result.output


def test_assistant_url_metadata_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        assistant_cli,
        "fetch_url_metadata",
        lambda _url: UrlMetadata(
            url="https://github.com/PKU-YuanGroup/Helios",
            title="PKU-YuanGroup/Helios",
            description="Code for the Helios paper.",
            image_url="https://example.com/helios.png",
            favicon="https://example.com/favicon.svg",
            site_name="GitHub",
            author="PKU-YuanGroup",
            raw={"title": "PKU-YuanGroup/Helios"},
        ),
    )

    result = runner.invoke(
        cli,
        ["assistant", "url-metadata", "https://github.com/PKU-YuanGroup/Helios"],
    )

    assert result.exit_code == 0
    assert "Assistant URL Metadata" in result.output
    assert "GitHub" in result.output


def test_folders_list_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        folders_cli,
        "fetch_folders",
        lambda: [
            Folder(
                id="folder-reading",
                name="Reading List",
                folder_type="collection",
                order=1,
                parent_id=None,
                sharing_status="private",
                papers=[
                    FolderPaper(
                        paper_group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
                        universal_paper_id="2603.04379",
                        canonical_id="2603.04379v1",
                        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
                        title="Helios",
                        abstract="We introduce Helios.",
                        topics=["Computer Science"],
                        raw={},
                    )
                ],
                raw={},
            )
        ],
    )

    result = runner.invoke(cli, ["folders", "list", "--papers"])

    assert result.exit_code == 0
    assert "Reading List" in result.output
    assert "Helios" in result.output


def test_folders_show_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        folders_cli,
        "fetch_folder",
        lambda _selector: Folder(
            id="folder-reading",
            name="Reading List",
            folder_type="collection",
            order=1,
            parent_id=None,
            sharing_status="private",
            papers=[
                FolderPaper(
                    paper_group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
                    universal_paper_id="2603.04379",
                    canonical_id="2603.04379v1",
                    version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
                    title="Helios",
                    abstract="We introduce Helios.",
                    topics=["Computer Science"],
                    authors=["Shenghai Yuan"],
                    raw={},
                )
            ],
            raw={},
        ),
    )

    result = runner.invoke(cli, ["folders", "show", "Reading List"])

    assert result.exit_code == 0
    assert "Reading List" in result.output
    assert "folder-reading" in result.output
    assert "Helios" in result.output


def test_paper_folders_list_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        paper_cli,
        "fetch_paper_folder_membership",
        lambda _identifier: (
            "1706.03762v7",
            "015c9ef4-ac30-768d-928b-847320902575",
            [
                Folder(
                    id="folder-completed",
                    name="Completed",
                    folder_type="default-completed",
                    order=2,
                    parent_id=None,
                    sharing_status="private",
                    papers=[
                        FolderPaper(
                            paper_group_id="015c9ef4-ac30-768d-928b-847320902575",
                            universal_paper_id="1706.03762",
                            canonical_id="1706.03762v7",
                            version_id="0189b531-a930-7613-9d2e-dd918c8435a5",
                            title="Attention Is All You Need",
                            abstract=None,
                            topics=["transformers"],
                            raw={},
                        )
                    ],
                    raw={},
                )
            ],
        ),
    )

    result = runner.invoke(cli, ["paper", "folders", "list", "1706.03762"])

    assert result.exit_code == 0
    assert "Folder Membership for 1706.03762v7" in result.output
    assert "Completed" in result.output
    assert "yes" in result.output


def test_paper_folders_list_resolution_error_shows_id_guidance(monkeypatch) -> None:
    runner = CliRunner()

    class _DummyPapers:
        async def resolve(self, _identifier: str) -> ResolvedPaper:
            return ResolvedPaper(
                input_id="0189b531-a930-7613-9d2e-dd918c8435a5",
                versionless_id=None,
                canonical_id=None,
                version_id="0189b531-a930-7613-9d2e-dd918c8435a5",
                group_id=None,
            )

    class _DummyFolders:
        async def list(self):
            return []

    class _DummyClient:
        def __init__(self) -> None:
            self.papers = _DummyPapers()
            self.folders = _DummyFolders()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
            return None

    monkeypatch.setattr(paper_cli, "make_client", lambda: _DummyClient())

    result = runner.invoke(
        cli, ["paper", "folders", "list", "0189b531-a930-7613-9d2e-dd918c8435a5"]
    )

    assert result.exit_code != 0
    assert "requires a bare or versioned arXiv ID" in result.output
    assert "alphaxiv paper folders list 1706.03762" in result.output
    assert "alphaxiv paper show 1706.03762" in result.output


def test_paper_folders_add_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        paper_cli,
        "add_paper_to_folder",
        lambda _identifier, _folder: Folder(
            id="folder-reading",
            name="Reading List",
            folder_type="collection",
            order=1,
            parent_id=None,
            sharing_status="private",
            papers=[],
            raw={},
        ),
    )

    result = runner.invoke(cli, ["paper", "folders", "add", "1706.03762", "Reading List", "--yes"])

    assert result.exit_code == 0
    assert "Saved" in result.output
    assert "Reading List" in result.output


def test_paper_folders_add_usage_error_shows_examples() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["paper", "folders", "add"])

    assert result.exit_code != 0
    assert "Expected either <folder> or <paper-id> <folder>." in result.output
    assert 'alphaxiv paper folders add "Want to read"' in result.output
    assert 'alphaxiv paper folders add 1706.03762 "Want to read"' in result.output


def test_paper_folders_remove_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        paper_cli,
        "remove_paper_from_folder",
        lambda _identifier, _folder: Folder(
            id="folder-reading",
            name="Reading List",
            folder_type="collection",
            order=1,
            parent_id=None,
            sharing_status="private",
            papers=[],
            raw={},
        ),
    )

    result = runner.invoke(
        cli,
        ["paper", "folders", "remove", "1706.03762", "Reading List", "--yes"],
    )

    assert result.exit_code == 0
    assert "Removed" in result.output
    assert "Reading List" in result.output


def test_comment_reply_usage_error_shows_examples() -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["paper", "comments", "reply", "paper-id", "comment-id", "extra", "--body", "Thanks"],
    )

    assert result.exit_code != 0
    assert "Expected either <comment-id> or <paper-id> <comment-id>." in result.output
    assert 'alphaxiv paper comments reply comment-root --body "Thanks"' in result.output
    assert 'alphaxiv paper comments reply 1706.03762 comment-root --body "Thanks"' in result.output
