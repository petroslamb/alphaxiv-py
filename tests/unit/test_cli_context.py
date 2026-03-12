from __future__ import annotations

import importlib
from datetime import datetime, timezone

from click.testing import CliRunner

from alphaxiv.alphaxiv_cli import cli
from alphaxiv.auth import SavedAuth, load_saved_auth, save_auth
from alphaxiv.paths import get_auth_path, get_browser_profile_path
from alphaxiv.types import (
    FeedCard,
    HomepageSearchResults,
    OrganizationResult,
    OverviewStatus,
    OverviewSummary,
    OverviewTranslationStatus,
    PaperFullText,
    PaperTranscript,
    PaperOverview,
    PaperTextPage,
    PodcastTranscriptLine,
    ResolvedPaper,
    SearchResult,
)

explore_cli = importlib.import_module("alphaxiv.cli.explore")
paper_cli = importlib.import_module("alphaxiv.cli.paper")
session_cli = importlib.import_module("alphaxiv.cli.session")


def test_login_command_saves_auth(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    saved_auth = SavedAuth(
        access_token="test-token",
        created_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
        expires_at=None,
        user={"name": "Petros", "email": "petros@example.com"},
    )
    monkeypatch.setattr(session_cli, "authenticate_with_browser", lambda: saved_auth)

    result = runner.invoke(cli, ["login"])

    assert result.exit_code == 0
    assert "Authentication saved" in result.output
    loaded = load_saved_auth()
    assert loaded is not None
    assert loaded.email == "petros@example.com"


def test_logout_command_clears_saved_auth(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_auth(
        SavedAuth(
            access_token="test-token",
            created_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
            expires_at=None,
            user={"email": "petros@example.com"},
        )
    )
    browser_profile = get_browser_profile_path()
    browser_profile.mkdir(parents=True, exist_ok=True)
    (browser_profile / "marker.txt").write_text("profile")

    result = runner.invoke(cli, ["logout", "--clear-browser-profile"])

    assert result.exit_code == 0
    assert "Removed saved alphaXiv authentication" in result.output
    assert not get_auth_path().exists()
    assert not browser_profile.exists()


def test_use_and_status(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    resolved = ResolvedPaper(
        input_id="2603.04379",
        versionless_id="2603.04379",
        canonical_id="2603.04379v1",
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
    )
    monkeypatch.setattr(session_cli, "resolve_paper_identifier", lambda _: resolved)

    result = runner.invoke(cli, ["use", "2603.04379"])
    assert result.exit_code == 0
    assert "Current paper set" in result.output

    status = runner.invoke(cli, ["status"])
    assert status.exit_code == 0
    assert "Not logged in to alphaXiv" in status.output
    assert "2603.04379v1" in status.output


def test_status_shows_saved_auth(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_auth(
        SavedAuth(
            access_token="test-token",
            created_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
            expires_at=None,
            user={"name": "Petros", "email": "petros@example.com"},
        )
    )
    monkeypatch.setattr(session_cli, "fetch_preferred_model", lambda _saved_auth: "claude-4.6-sonnet")

    status = runner.invoke(cli, ["status"])

    assert status.exit_code == 0
    assert "alphaXiv Authentication" in status.output
    assert "petros@example.com" in status.output
    assert "claude-4.6-sonnet" in status.output


def test_overview_uses_current_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    resolved = ResolvedPaper(
        input_id="2603.04379",
        versionless_id="2603.04379",
        canonical_id="2603.04379v1",
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
    )
    monkeypatch.setattr(session_cli, "resolve_paper_identifier", lambda _: resolved)
    runner.invoke(cli, ["use", "2603.04379"])

    overview = PaperOverview(
        version_id=resolved.version_id or "",
        language="en",
        title="Helios",
        abstract="We introduce Helios.",
        summary=OverviewSummary(
            summary="Fast video generation",
            original_problem=[],
            solution=[],
            key_insights=[],
            results=[],
            raw={},
        ),
        overview_markdown="## Problem",
        intermediate_report=None,
        citations=[],
        raw={},
    )
    monkeypatch.setattr(paper_cli, "fetch_overview", lambda _identifier, language="en": overview)

    result = runner.invoke(cli, ["overview"])
    assert result.exit_code == 0
    assert "Helios" in result.output
    assert "Fast video generation" in result.output


def test_overview_machine_mode(monkeypatch) -> None:
    runner = CliRunner()
    overview = PaperOverview(
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        language="en",
        title="Helios",
        abstract="We introduce Helios.",
        summary=None,
        overview_markdown="## Research Paper Analysis\n\nMachine readable body",
        intermediate_report=None,
        citations=[],
        raw={},
    )
    monkeypatch.setattr(paper_cli, "fetch_overview", lambda _identifier, language="en": overview)

    result = runner.invoke(cli, ["overview", "2603.04379", "--machine"])
    assert result.exit_code == 0
    assert "Machine readable body" in result.output
    assert "Summary" not in result.output


def test_overview_status_command(monkeypatch) -> None:
    runner = CliRunner()
    status = OverviewStatus(
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        state="done",
        updated_at=None,
        translations={
            "en": OverviewTranslationStatus(
                language="en",
                state="done",
                requested_at=None,
                updated_at=None,
                error=None,
                raw={},
            )
        },
        raw={},
    )
    monkeypatch.setattr(paper_cli, "fetch_overview_status", lambda _identifier: status)

    result = runner.invoke(cli, ["overview-status", "2603.04379"])
    assert result.exit_code == 0
    assert "Overview Status" in result.output
    assert "done" in result.output
    assert "en" in result.output


def test_paper_text_uses_current_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    resolved = ResolvedPaper(
        input_id="2603.04379",
        versionless_id="2603.04379",
        canonical_id="2603.04379v1",
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
    )
    monkeypatch.setattr(session_cli, "resolve_paper_identifier", lambda _: resolved)
    runner.invoke(cli, ["use", "2603.04379"])

    full_text = PaperFullText(
        resolved=resolved,
        pages=[
            PaperTextPage(page_number=1, text="Abstract\nWe introduce Helios.", raw={}),
            PaperTextPage(page_number=2, text="1 Introduction\nLong video generation...", raw={}),
        ],
        raw={},
    )
    monkeypatch.setattr(paper_cli, "fetch_full_text", lambda _identifier: full_text)

    result = runner.invoke(cli, ["paper", "text", "--page", "2"])
    assert result.exit_code == 0
    assert "2603.04379v1" in result.output
    assert "Page 2" in result.output
    assert "Long video generation" in result.output


def test_resources_bibtex_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        paper_cli,
        "fetch_bibtex",
        lambda _identifier: "@article{helios,\n  title={Helios}\n}",
    )

    result = runner.invoke(cli, ["resources", "2603.04379", "--bibtex"])
    assert result.exit_code == 0
    assert "@article{helios" in result.output


def test_resources_transcript_command(monkeypatch) -> None:
    runner = CliRunner()
    resolved = ResolvedPaper(
        input_id="2603.04379",
        versionless_id="2603.04379",
        canonical_id="2603.04379v1",
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
    )
    transcript = PaperTranscript(
        resolved=resolved,
        transcript_url="https://paper-podcasts.alphaxiv.org/019cbc05-f11c-75c7-a13b-b028107d6a76/transcript.json",
        lines=[
            PodcastTranscriptLine(
                speaker="John",
                line="Welcome to the Helios summary.",
                raw={},
            )
        ],
        raw=[],
    )
    monkeypatch.setattr(paper_cli, "fetch_transcript", lambda _identifier: transcript)

    result = runner.invoke(cli, ["resources", "2603.04379", "--transcript"])
    assert result.exit_code == 0
    assert "Audio Transcript" in result.output
    assert "John:" in result.output
    assert "Helios summary" in result.output


def test_search_shows_topics_and_organizations(monkeypatch) -> None:
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

    result = runner.invoke(cli, ["search", "reinforcement learning"])
    assert result.exit_code == 0
    assert "Suggested Topics" in result.output
    assert "deep-reinforcement-learning" in result.output
    assert "MIT" in result.output


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

    result = runner.invoke(cli, ["search-papers", "helios"])
    assert result.exit_code == 0
    assert "Paper Search Results for: helios" in result.output
    assert "2603.04379" in result.output


def test_search_organizations_command(monkeypatch) -> None:
    runner = CliRunner()
    organizations = [
        OrganizationResult(id="org-mit", name="MIT", image=None, slug="mit", raw={})
    ]
    monkeypatch.setattr(explore_cli, "fetch_organization_search", lambda _query: organizations)

    result = runner.invoke(cli, ["search-organizations", "mit"])
    assert result.exit_code == 0
    assert "MIT" in result.output
    assert "mit" in result.output
    assert "MIT" in result.output


def test_search_topics_command(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        explore_cli, "fetch_topic_search", lambda _query: ["deep-reinforcement-learning"]
    )

    result = runner.invoke(cli, ["search-topics", "reinforcement learning"])
    assert result.exit_code == 0
    assert "Suggested Topics" in result.output
    assert "deep-reinforcement-learning" in result.output
