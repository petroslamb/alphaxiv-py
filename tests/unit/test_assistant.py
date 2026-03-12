from __future__ import annotations

from datetime import datetime, timezone

from click.testing import CliRunner

from alphaxiv._core import ClientCore
from alphaxiv.alphaxiv_cli import cli
from alphaxiv.assistant import AssistantAPI
from alphaxiv.cli.helpers import load_assistant_context, save_assistant_context
from alphaxiv.types import (
    AssistantContext,
    AssistantMessage,
    AssistantRun,
    AssistantSession,
    ResolvedPaper,
)

import importlib

assistant_cli = importlib.import_module("alphaxiv.cli.assistant")


def test_assistant_context_round_trip(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    paper = ResolvedPaper(
        input_id="2603.04379",
        versionless_id="2603.04379",
        canonical_id="2603.04379v1",
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
    )
    context = AssistantContext(
        session_id="session-1",
        variant="paper",
        paper=paper,
        newest_message_at=datetime(2026, 3, 12, 8, 0, tzinfo=timezone.utc),
        title="Helios chat",
    )

    save_assistant_context(context)
    loaded = load_assistant_context()

    assert loaded == context


def test_parse_sse_event_delta_and_raw() -> None:
    assistant = AssistantAPI(ClientCore(authorization="Bearer test-token"))

    event = assistant._parse_sse_event(
        ['data: {"type":"delta_output_text","delta":"Hello","index":0}']
    )
    raw_event = assistant._parse_sse_event(["data: not-json"])

    assert event is not None
    assert event.event_type == "delta_output_text"
    assert event.text == "Hello"
    assert raw_event is not None
    assert raw_event.event_type == "raw"
    assert raw_event.content == "not-json"


def test_extract_preferred_model() -> None:
    assistant = AssistantAPI(ClientCore(authorization="Bearer test-token"))

    model = assistant._extract_preferred_model(
        {"user": {"preferences": {"base": {"preferredLlmModel": "claude-4.6-sonnet"}}}}
    )

    assert model == "claude-4.6-sonnet"


def test_normalize_model_label_and_passthrough() -> None:
    assistant = AssistantAPI(ClientCore(authorization="Bearer test-token"))

    assert assistant._normalize_model("Claude 4.6 Sonnet") == "claude-4.6-sonnet"
    assert assistant._normalize_model("my-new-model") == "my-new-model"


def test_assistant_cli_start_saves_context(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    run = AssistantRun(
        session_id="session-new",
        session_title="Helios follow-up",
        newest_message_at=datetime(2026, 3, 12, 8, 0, tzinfo=timezone.utc),
        variant="homepage",
        paper=None,
        message="Tell me about Helios.",
        model="claude-4.6-sonnet",
        thinking=True,
        web_search="off",
        output_text="Helios is a video model.",
        reasoning_text="Searching alphaXiv...",
        error_message=None,
        events=[],
        raw=[],
    )
    monkeypatch.setattr(assistant_cli, "run_assistant_chat", lambda **_kwargs: run)

    result = runner.invoke(cli, ["assistant", "start", "Tell me about Helios."])

    assert result.exit_code == 0
    assert "Current assistant chat set" in result.output
    context = load_assistant_context()
    assert context is not None
    assert context.session_id == "session-new"


def test_assistant_cli_history_uses_current_context(monkeypatch, tmp_path) -> None:
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
    messages = [
        AssistantMessage(
            id="message-input",
            message_type="input_text",
            parent_message_id=None,
            selected_at=datetime(2026, 3, 12, 8, 0, tzinfo=timezone.utc),
            tool_use_id=None,
            kind=None,
            content="What is Helios?",
            model="claude-4.6-sonnet",
            feedback_type=None,
            feedback_category=None,
            feedback_details=None,
            raw={"type": "input_text", "content": "What is Helios?"},
        ),
        AssistantMessage(
            id="message-output",
            message_type="output_text",
            parent_message_id="message-input",
            selected_at=datetime(2026, 3, 12, 8, 1, tzinfo=timezone.utc),
            tool_use_id=None,
            kind=None,
            content="Helios is a video model.",
            model="claude-4.6-sonnet",
            feedback_type=None,
            feedback_category=None,
            feedback_details=None,
            raw={"type": "output_text", "content": "Helios is a video model."},
        ),
    ]
    monkeypatch.setattr(assistant_cli, "fetch_history", lambda _session_id: messages)

    result = runner.invoke(cli, ["assistant", "history"])

    assert result.exit_code == 0
    assert "Assistant History" in result.output
    assert "What is Helios?" in result.output
    assert "Helios is a video model." in result.output


def test_assistant_cli_history_raw(monkeypatch, tmp_path) -> None:
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
    messages = [
        AssistantMessage(
            id="message-output",
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
            raw={"type": "output_text", "content": "Helios is a video model."},
        )
    ]
    monkeypatch.setattr(assistant_cli, "fetch_history", lambda _session_id: messages)

    result = runner.invoke(cli, ["assistant", "history", "--raw"])

    assert result.exit_code == 0
    assert '"type": "output_text"' in result.output


def test_assistant_set_model_cli(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(assistant_cli, "set_model_preference", lambda _model: "claude-4.6-sonnet")

    result = runner.invoke(cli, ["assistant", "set-model", "Claude 4.6 Sonnet"])

    assert result.exit_code == 0
    assert "Preferred assistant model set" in result.output
    assert "claude-4.6-sonnet" in result.output


def test_assistant_models_command_removed() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["assistant", "models"])

    assert result.exit_code != 0
    assert "No such command 'models'" in result.output
