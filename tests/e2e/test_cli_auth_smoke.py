from __future__ import annotations

import pytest
from tests.e2e.helpers import (
    SMOKE_PAPER_ID,
    assert_cli_ok,
    fetch_comment_by_id,
    fetch_first_comment_id,
    fetch_folders,
    fetch_paper_group_id,
    find_folder_membership_target,
    invoke_cli,
    require_live_auth_smoke,
    seed_saved_api_key,
    wait_for_comment_upvote_state,
    wait_for_folder_membership_state,
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


def test_cli_auth_folder_show_and_paper_membership_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    api_key = require_live_auth_smoke()
    seed_saved_api_key(cli_runner, isolated_cli_env, api_key)

    folders = fetch_folders(api_key)
    if not folders:
        pytest.skip("No live alphaXiv folders were returned.")
    folder = folders[0]

    show_result = invoke_cli(cli_runner, ["folders", "show", folder.id], env=isolated_cli_env)
    assert_cli_ok(show_result, "folders", "show", folder.id)
    assert folder.name in show_result.output
    assert folder.id in show_result.output

    membership_result = invoke_cli(
        cli_runner,
        ["paper", "folders", "list", SMOKE_PAPER_ID],
        env=isolated_cli_env,
    )
    assert_cli_ok(membership_result, "paper", "folders", "list", SMOKE_PAPER_ID)
    assert "Folder Membership for" in membership_result.output
    assert SMOKE_PAPER_ID in membership_result.output
    assert folder.name in membership_result.output


def test_cli_auth_paper_folder_membership_is_reversible(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    api_key = require_live_auth_smoke()
    seed_saved_api_key(cli_runner, isolated_cli_env, api_key)

    target_folder, initially_contains = find_folder_membership_target(
        api_key, paper_id=SMOKE_PAPER_ID
    )
    paper_group_id = fetch_paper_group_id(api_key, SMOKE_PAPER_ID)
    folder_selector = target_folder.id

    if initially_contains:
        first_args = ["paper", "folders", "remove", SMOKE_PAPER_ID, folder_selector, "--yes"]
        second_args = ["paper", "folders", "add", SMOKE_PAPER_ID, folder_selector, "--yes"]
        first_expected = False
        second_expected = True
        first_label = "Removed"
        second_label = "Saved"
    else:
        first_args = ["paper", "folders", "add", SMOKE_PAPER_ID, folder_selector, "--yes"]
        second_args = ["paper", "folders", "remove", SMOKE_PAPER_ID, folder_selector, "--yes"]
        first_expected = True
        second_expected = False
        first_label = "Saved"
        second_label = "Removed"

    first_result = invoke_cli(cli_runner, first_args, env=isolated_cli_env)
    assert_cli_ok(first_result, *first_args)
    assert first_label in first_result.output
    wait_for_folder_membership_state(
        api_key,
        folder_selector,
        paper_group_id,
        first_expected,
    )

    second_result = invoke_cli(cli_runner, second_args, env=isolated_cli_env)
    assert_cli_ok(second_result, *second_args)
    assert second_label in second_result.output
    restored = wait_for_folder_membership_state(
        api_key,
        folder_selector,
        paper_group_id,
        second_expected,
    )
    assert restored.contains_paper_group_id(paper_group_id) is initially_contains


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
