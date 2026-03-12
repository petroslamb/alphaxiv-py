from __future__ import annotations

import pytest
from tests.e2e.helpers import (
    SMOKE_PAPER_ID,
    assert_cli_ok,
    fetch_comment_by_id,
    fetch_first_comment_id,
    invoke_cli,
    require_live_auth_smoke,
    seed_saved_api_key,
    wait_for_comment_upvote_state,
)

pytestmark = pytest.mark.e2e


def test_cli_auth_status_and_assistant_reads_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    api_key = require_live_auth_smoke()
    seed_saved_api_key(cli_runner, isolated_cli_env, api_key)

    status_result = invoke_cli(cli_runner, ["auth", "status"], env=isolated_cli_env)
    assert_cli_ok(status_result, "auth", "status")
    assert "alphaXiv API Key" in status_result.output
    assert "configured" in status_result.output
    assert "saved" in status_result.output

    model_result = invoke_cli(cli_runner, ["assistant", "model"], env=isolated_cli_env)
    assert_cli_ok(model_result, "assistant", "model")
    assert "Preferred assistant model:" in model_result.output

    sessions_result = invoke_cli(
        cli_runner,
        ["assistant", "list", "--limit", "1"],
        env=isolated_cli_env,
    )
    assert_cli_ok(sessions_result, "assistant", "list", "--limit", "1")
    assert "Assistant Sessions" in sessions_result.output


def test_cli_auth_folders_list_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    api_key = require_live_auth_smoke()
    seed_saved_api_key(cli_runner, isolated_cli_env, api_key)

    folders_result = invoke_cli(cli_runner, ["folders", "list"], env=isolated_cli_env)
    assert_cli_ok(folders_result, "folders", "list")
    assert "alphaXiv Folders" in folders_result.output


def test_cli_auth_comment_upvote_is_reversible(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    api_key = require_live_auth_smoke()
    seed_saved_api_key(cli_runner, isolated_cli_env, api_key)

    comment_id = fetch_first_comment_id(api_key, SMOKE_PAPER_ID)
    original_state = fetch_comment_by_id(api_key, comment_id, paper_id=SMOKE_PAPER_ID).has_upvoted

    first_toggle = invoke_cli(
        cli_runner,
        ["paper", "comments", "upvote", comment_id, "--yes"],
        env=isolated_cli_env,
    )
    assert_cli_ok(first_toggle, "paper", "comments", "upvote", comment_id, "--yes")
    assert "Toggled comment upvote for" in first_toggle.output
    wait_for_comment_upvote_state(
        api_key,
        comment_id,
        not original_state,
        paper_id=SMOKE_PAPER_ID,
    )

    second_toggle = invoke_cli(
        cli_runner,
        ["paper", "comments", "upvote", comment_id, "--yes"],
        env=isolated_cli_env,
    )
    assert_cli_ok(second_toggle, "paper", "comments", "upvote", comment_id, "--yes")
    restored = wait_for_comment_upvote_state(
        api_key,
        comment_id,
        original_state,
        paper_id=SMOKE_PAPER_ID,
    )
    assert restored.has_upvoted is original_state
