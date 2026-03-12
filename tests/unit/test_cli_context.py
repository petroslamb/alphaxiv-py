from __future__ import annotations

import importlib
from datetime import UTC, datetime

from click.testing import CliRunner

from alphaxiv.alphaxiv_cli import cli
from alphaxiv.auth import SavedApiKey, build_saved_api_key, load_saved_api_key, save_api_key
from alphaxiv.cli.helpers import (
    load_assistant_context,
    load_context,
    save_assistant_context,
    save_context,
)
from alphaxiv.paths import (
    get_api_key_path,
    get_assistant_context_path,
    get_context_path,
    get_legacy_auth_path,
)
from alphaxiv.types import (
    AssistantContext,
    OverviewStatus,
    OverviewSummary,
    OverviewTranslationStatus,
    Paper,
    PaperFullText,
    PaperGroup,
    PaperOverview,
    PaperTextPage,
    PaperTranscript,
    PaperVersion,
    PodcastTranscriptLine,
    ResolvedPaper,
)

assistant_cli = importlib.import_module("alphaxiv.cli.assistant")
auth_cli = importlib.import_module("alphaxiv.cli.auth")
context_cli = importlib.import_module("alphaxiv.cli.session")
paper_cli = importlib.import_module("alphaxiv.cli.paper")


def _resolved(identifier: str, *, title: str | None = None) -> ResolvedPaper:
    return ResolvedPaper(
        input_id=identifier,
        versionless_id="2603.04379",
        canonical_id="2603.04379v1",
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
        title=title,
    )


def test_auth_set_api_key_command_saves_auth(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    saved_auth = SavedApiKey(
        api_key="axv1_test-token",
        saved_at=datetime(2026, 3, 11, tzinfo=UTC),
        user={"name": "Petros", "email": "petros@example.com"},
    )
    monkeypatch.setattr(auth_cli, "authenticate_with_api_key", lambda _api_key: saved_auth)

    result = runner.invoke(cli, ["auth", "set-api-key", "--api-key", "axv1_test-token"])

    assert result.exit_code == 0
    assert "API key saved" in result.output
    loaded = load_saved_api_key()
    assert loaded is not None
    assert loaded.email == "petros@example.com"


def test_auth_set_api_key_prompts_when_flag_missing(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    saved_auth = SavedApiKey(
        api_key="axv1_test-token",
        saved_at=datetime(2026, 3, 11, tzinfo=UTC),
        user={"name": "Petros", "email": "petros@example.com"},
    )
    monkeypatch.setattr(auth_cli, "authenticate_with_api_key", lambda _api_key: saved_auth)

    result = runner.invoke(cli, ["auth", "set-api-key"], input="axv1_test-token\n")

    assert result.exit_code == 0
    assert "alphaXiv API key" in result.output
    assert "API key saved" in result.output
    loaded = load_saved_api_key()
    assert loaded is not None
    assert loaded.api_key == "axv1_test-token"


def test_auth_clear_command_removes_saved_and_legacy_auth(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_api_key(
        build_saved_api_key(
            "axv1_test-token",
            user={"email": "petros@example.com"},
            saved_at=datetime(2026, 3, 11, tzinfo=UTC),
        )
    )
    legacy_auth_path = get_legacy_auth_path()
    legacy_auth_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_auth_path.write_text('{"access_token": "legacy-token"}')

    result = runner.invoke(cli, ["auth", "clear"])

    assert result.exit_code == 0
    assert "Removed local alphaXiv auth files" in result.output
    assert not get_api_key_path().exists()
    assert not legacy_auth_path.exists()


def test_auth_status_shows_saved_api_key_without_model(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_api_key(
        build_saved_api_key(
            "axv1_test-token",
            user={"name": "Petros", "email": "petros@example.com"},
            saved_at=datetime(2026, 3, 11, tzinfo=UTC),
        )
    )

    status = runner.invoke(cli, ["auth", "status"])

    assert status.exit_code == 0
    assert "alphaXiv API Key" in status.output
    assert "petros@example.com" in status.output
    assert "saved" in status.output
    assert "axv1_test-token" not in status.output
    assert "axv1_test-to" in status.output
    assert "Preferred Model" not in status.output


def test_auth_status_warns_about_legacy_auth(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    legacy_auth_path = get_legacy_auth_path()
    legacy_auth_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_auth_path.write_text('{"access_token": "legacy-token"}')

    status = runner.invoke(cli, ["auth", "status"])

    assert status.exit_code == 0
    assert "Legacy auth.json found but ignored" in status.output


def test_context_use_paper_and_show(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    resolved = _resolved("2603.04379", title="Helios: Real Real-Time Long Video Generation Model")
    monkeypatch.setattr(context_cli, "resolve_paper_identifier", lambda _: resolved)

    result = runner.invoke(cli, ["context", "use", "paper", "2603.04379"])

    assert result.exit_code == 0
    assert "Current paper set" in result.output

    status = runner.invoke(cli, ["context", "show"])
    assert status.exit_code == 0
    assert "Current Paper Context" in status.output
    assert "Helios: Real Real-Time Long Video Generation Model" in status.output
    assert "2603.04379v1" in status.output
    assert "Current Assistant Context" in status.output
    assert "No current assistant chat is set" in status.output


def test_context_show_paper_hydrates_missing_title(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_context(_resolved("2603.04379", title=None))

    def _run_async(awaitable):
        awaitable.close()
        return "Helios"

    monkeypatch.setattr(context_cli, "run_async", _run_async)

    result = runner.invoke(cli, ["context", "show", "paper"])

    assert result.exit_code == 0
    assert "Helios" in result.output
    loaded = load_context()
    assert loaded is not None
    assert loaded.title == "Helios"


def test_context_use_assistant_saves_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    assistant_context = AssistantContext(
        session_id="session-existing",
        variant="paper",
        paper=_resolved("2603.04379", title="Helios"),
        newest_message_at=datetime(2026, 3, 12, 8, 0, tzinfo=UTC),
        title="Helios follow-up",
    )
    monkeypatch.setattr(
        assistant_cli, "resolve_context_for_session", lambda _session_id: assistant_context
    )

    result = runner.invoke(cli, ["context", "use", "assistant", "session-existing"])

    assert result.exit_code == 0
    assert "Current assistant chat set" in result.output
    loaded = load_assistant_context()
    assert loaded == assistant_context


def test_context_clear_targets_right_files(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_context(_resolved("2603.04379", title="Helios"))
    save_assistant_context(
        AssistantContext(
            session_id="session-existing",
            variant="homepage",
            paper=None,
            newest_message_at=None,
            title="Earlier chat",
        )
    )

    paper_clear = runner.invoke(cli, ["context", "clear", "paper"])
    assert paper_clear.exit_code == 0
    assert "Cleared current paper context" in paper_clear.output
    assert not get_context_path().exists()
    assert get_assistant_context_path().exists()

    assistant_clear = runner.invoke(cli, ["context", "clear", "assistant"])
    assert assistant_clear.exit_code == 0
    assert "Cleared current assistant chat context" in assistant_clear.output
    assert not get_assistant_context_path().exists()


def test_context_clear_without_target_clears_both(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_context(_resolved("2603.04379", title="Helios"))
    save_assistant_context(
        AssistantContext(
            session_id="session-existing",
            variant="homepage",
            paper=None,
            newest_message_at=None,
            title="Earlier chat",
        )
    )

    result = runner.invoke(cli, ["context", "clear"])

    assert result.exit_code == 0
    assert "Cleared current paper context" in result.output
    assert "Cleared current assistant chat context" in result.output
    assert not get_context_path().exists()
    assert not get_assistant_context_path().exists()


def test_overview_uses_current_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    resolved = _resolved("2603.04379", title="Helios")
    monkeypatch.setattr(context_cli, "resolve_paper_identifier", lambda _: resolved)
    runner.invoke(cli, ["context", "use", "paper", "2603.04379"])

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

    result = runner.invoke(cli, ["paper", "overview"])
    assert result.exit_code == 0
    assert "Helios" in result.output
    assert "Fast video generation" in result.output


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

    result = runner.invoke(cli, ["paper", "overview-status", "2603.04379"])
    assert result.exit_code == 0
    assert "Overview Status" in result.output
    assert "done" in result.output
    assert "en" in result.output


def test_paper_abstract_uses_current_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    resolved = _resolved("2603.04379", title="Helios: Real Real-Time Long Video Generation Model")
    monkeypatch.setattr(context_cli, "resolve_paper_identifier", lambda _: resolved)
    runner.invoke(cli, ["context", "use", "paper", "2603.04379"])

    paper = Paper(
        resolved=resolved,
        version=PaperVersion(
            id=resolved.version_id or "",
            version_label="v1",
            version_order=1,
            title="Helios: Real Real-Time Long Video Generation Model",
            abstract="We introduce Helios.",
            publication_date=None,
            license_url=None,
            created_at=None,
            updated_at=None,
            is_hidden=False,
            image_url=None,
            universal_paper_id="2603.04379",
            raw={},
        ),
        group=PaperGroup(
            id=resolved.group_id or "",
            universal_paper_id="2603.04379",
            title="Helios: Real Real-Time Long Video Generation Model",
            created_at=None,
            updated_at=None,
            topics=[],
            metrics=None,
            podcast_path=None,
            source_name=None,
            source_url=None,
            is_hidden=False,
            first_publication_date=None,
            variant=None,
            citation=None,
            resources=[],
            raw={},
        ),
        authors=[],
        verified_authors=[],
        pdf_url=None,
        implementation=None,
        marimo_implementation=None,
        organization_info=[],
        comments=[],
        raw={},
    )
    monkeypatch.setattr(paper_cli, "fetch_paper", lambda _identifier: paper)

    result = runner.invoke(cli, ["paper", "abstract"])
    assert result.exit_code == 0
    assert "Helios: Real Real-Time Long Video Generation Model" in result.output
    assert "We introduce Helios." in result.output


def test_paper_summary_uses_current_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    resolved = _resolved("2603.04379", title="Helios")
    monkeypatch.setattr(context_cli, "resolve_paper_identifier", lambda _: resolved)
    runner.invoke(cli, ["context", "use", "paper", "2603.04379"])

    overview = PaperOverview(
        version_id=resolved.version_id or "",
        language="en",
        title="Helios",
        abstract="We introduce Helios.",
        summary=OverviewSummary(
            summary="Fast video generation",
            original_problem=["Long videos drift."],
            solution=["Unified History Injection."],
            key_insights=["Relative RoPE stabilizes long contexts."],
            results=["19.53 FPS on H100."],
            raw={"summary": "Fast video generation"},
        ),
        overview_markdown="## Problem",
        intermediate_report=None,
        citations=[],
        raw={},
    )
    monkeypatch.setattr(paper_cli, "fetch_overview", lambda _identifier, language="en": overview)

    result = runner.invoke(cli, ["paper", "summary"])
    assert result.exit_code == 0
    assert "Fast video generation" in result.output
    assert "Original Problem" in result.output
    assert "Solution" in result.output
    assert "Results" in result.output


def test_paper_text_uses_current_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    resolved = _resolved("2603.04379")
    monkeypatch.setattr(context_cli, "resolve_paper_identifier", lambda _: resolved)
    runner.invoke(cli, ["context", "use", "paper", "2603.04379"])

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

    result = runner.invoke(cli, ["paper", "resources", "2603.04379", "--bibtex"])
    assert result.exit_code == 0
    assert "@article{helios" in result.output


def test_resources_transcript_command(monkeypatch) -> None:
    runner = CliRunner()
    resolved = _resolved("2603.04379")
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

    result = runner.invoke(cli, ["paper", "resources", "2603.04379", "--transcript"])
    assert result.exit_code == 0
    assert "Audio Transcript" in result.output
    assert "John:" in result.output
    assert "Helios summary" in result.output
