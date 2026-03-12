from __future__ import annotations

import secrets

import pytest
from tests.e2e.helpers import (
    SMOKE_PAPER_ID,
    assert_cli_ok,
    invoke_cli,
    invoke_cli_with_retries,
    load_saved_assistant_context,
    require_live_assistant_write_smoke,
    seed_saved_api_key,
)

pytestmark = pytest.mark.e2e


def test_cli_assistant_start_history_and_reply_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    api_key = require_live_assistant_write_smoke()
    seed_saved_api_key(cli_runner, isolated_cli_env, api_key)

    nonce = secrets.token_hex(4)
    prompt_prefix = f"alphaxiv-py-smoke-{nonce}"
    reply_prefix = f"alphaxiv-py-smoke-reply-{nonce}"

    start_result = invoke_cli_with_retries(
        cli_runner,
        [
            "assistant",
            "start",
            "--paper",
            SMOKE_PAPER_ID,
            "--no-thinking",
            f"{prompt_prefix} What is the main contribution of this paper in one sentence?",
        ],
        env=isolated_cli_env,
        attempts=3,
        delay_seconds=2.0,
    )
    assert_cli_ok(
        start_result,
        "assistant",
        "start",
        "--paper",
        SMOKE_PAPER_ID,
        "--no-thinking",
        "<prompt>",
    )
    assert "Current assistant chat set:" in start_result.output

    assistant_context = load_saved_assistant_context()
    assert assistant_context is not None
    assert assistant_context.variant == "paper"
    assert assistant_context.paper is not None
    assert assistant_context.paper.versionless_id == SMOKE_PAPER_ID

    history_result = invoke_cli(cli_runner, ["assistant", "history"], env=isolated_cli_env)
    assert_cli_ok(history_result, "assistant", "history")
    assert "Assistant History" in history_result.output
    assert prompt_prefix in history_result.output

    reply_result = invoke_cli_with_retries(
        cli_runner,
        [
            "assistant",
            "reply",
            "--no-thinking",
            f"{reply_prefix} Summarize it in five words.",
        ],
        env=isolated_cli_env,
        attempts=3,
        delay_seconds=2.0,
    )
    assert_cli_ok(reply_result, "assistant", "reply", "--no-thinking", "<prompt>")

    updated_history = invoke_cli(cli_runner, ["assistant", "history"], env=isolated_cli_env)
    assert_cli_ok(updated_history, "assistant", "history")
    assert reply_prefix in updated_history.output
