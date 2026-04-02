from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from alphaxiv import AlphaXivClient
from alphaxiv.alphaxiv_cli import cli
from alphaxiv.auth import (
    ALPHAXIV_API_KEY_ENV,
    ensure_saved_browser_auth,
    load_saved_browser_auth,
    save_browser_auth,
)
from alphaxiv.types import AssistantContext, Folder, PaperComment

LIVE_SMOKE_ENV = "ALPHAXIV_RUN_E2E"
LIVE_ASSISTANT_WRITES_ENV = "ALPHAXIV_RUN_ASSISTANT_WRITES"
SMOKE_PAPER_ID = "1706.03762"


def require_live_smoke() -> None:
    if os.getenv(LIVE_SMOKE_ENV) != "1":
        pytest.skip("Set ALPHAXIV_RUN_E2E=1 to run live alphaXiv smoke tests.")


def require_live_auth_smoke() -> str:
    require_live_smoke()
    api_key = os.getenv(ALPHAXIV_API_KEY_ENV)
    if not api_key:
        pytest.skip("Set ALPHAXIV_API_KEY to run authenticated live alphaXiv smoke tests.")
    return api_key


def require_live_assistant_write_smoke() -> str:
    api_key = require_live_auth_smoke()
    if os.getenv(LIVE_ASSISTANT_WRITES_ENV) != "1":
        pytest.skip("Set ALPHAXIV_RUN_ASSISTANT_WRITES=1 to run live assistant write smoke tests.")
    return api_key


def build_cli_env(home: Path) -> dict[str, str]:
    return {
        "ALPHAXIV_HOME": str(home),
        ALPHAXIV_API_KEY_ENV: "",
    }


@contextmanager
def temporary_cli_env(env: dict[str, str]):
    previous: dict[str, str | None] = {key: os.environ.get(key) for key in env}
    try:
        for key, value in env.items():
            os.environ[key] = value
        yield
    finally:
        for key, previous_value in previous.items():
            if previous_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous_value


def invoke_cli(
    runner: CliRunner,
    args: list[str],
    *,
    env: dict[str, str],
    input_text: str | None = None,
) -> Result:
    return runner.invoke(cli, args, env=env, input=input_text)


def is_retryable_assistant_failure(result: Result) -> bool:
    message = result.output.strip() or repr(result.exception)
    retryable_markers = (
        "ReadTimeout",
        "Read timed out",
        "alphaXiv assistant returned an error",
        "Assistant backend failed",
    )
    return any(marker in message for marker in retryable_markers)


def invoke_cli_with_retries(
    runner: CliRunner,
    args: list[str],
    *,
    env: dict[str, str],
    attempts: int,
    delay_seconds: float,
) -> Result:
    result: Result | None = None
    for attempt in range(attempts):
        result = invoke_cli(runner, args, env=env)
        if result.exit_code == 0 or not is_retryable_assistant_failure(result):
            return result
        if attempt < attempts - 1:
            time.sleep(delay_seconds)
    assert result is not None
    return result


def assert_cli_ok(result: Result, *args: str) -> None:
    if result.exit_code == 0:
        return
    command = " ".join(args)
    message = result.output.strip() or repr(result.exception)
    raise AssertionError(f"CLI command failed: {command}\n{message}")


def seed_saved_api_key(runner: CliRunner, env: dict[str, str], api_key: str) -> Result:
    result = invoke_cli(
        runner,
        ["auth", "set-api-key", "--api-key", api_key],
        env=env,
    )
    assert_cli_ok(result, "auth", "set-api-key", "--api-key", "<redacted>")
    assert "API key saved" in result.output
    return result


def seed_saved_browser_auth(env: dict[str, str]) -> bool:
    source_env = {
        "ALPHAXIV_HOME": str(Path.home() / ".alphaxiv"),
        ALPHAXIV_API_KEY_ENV: "",
    }

    with temporary_cli_env(source_env):
        saved_auth = load_saved_browser_auth()
        if saved_auth is None:
            saved_auth = ensure_saved_browser_auth()
        if saved_auth is None or saved_auth.is_expired:
            return False

    with temporary_cli_env(env):
        save_browser_auth(saved_auth)
    return True


def seed_live_assistant_auth(runner: CliRunner, env: dict[str, str]) -> str:
    if seed_saved_browser_auth(env):
        return "browser"
    api_key = os.getenv(ALPHAXIV_API_KEY_ENV)
    if api_key:
        seed_saved_api_key(runner, env, api_key)
        return "api_key"
    pytest.skip("Set up alphaXiv browser auth or ALPHAXIV_API_KEY for assistant write smoke.")


def flatten_comments(comments: Iterable[PaperComment]) -> list[PaperComment]:
    flattened: list[PaperComment] = []
    for comment in comments:
        flattened.append(comment)
        if comment.responses:
            flattened.extend(flatten_comments(comment.responses))
    return flattened


async def _fetch_comments(api_key: str, paper_id: str) -> list[PaperComment]:
    async with AlphaXivClient(api_key=api_key) as client:
        return await client.papers.comments(paper_id)


def fetch_comments(api_key: str, paper_id: str = SMOKE_PAPER_ID) -> list[PaperComment]:
    return asyncio.run(_fetch_comments(api_key, paper_id))


def fetch_comment_by_id(
    api_key: str,
    comment_id: str,
    *,
    paper_id: str = SMOKE_PAPER_ID,
) -> PaperComment:
    for comment in flatten_comments(fetch_comments(api_key, paper_id)):
        if comment.id == comment_id:
            return comment
    raise AssertionError(f"Comment '{comment_id}' was not found in live comments for {paper_id}.")


def fetch_first_comment_id(api_key: str, paper_id: str = SMOKE_PAPER_ID) -> str:
    comments = flatten_comments(fetch_comments(api_key, paper_id))
    if not comments:
        raise AssertionError(f"No live comments were returned for {paper_id}.")
    return comments[0].id


def wait_for_comment_upvote_state(
    api_key: str,
    comment_id: str,
    expected: bool,
    *,
    paper_id: str = SMOKE_PAPER_ID,
    attempts: int = 5,
    delay_seconds: float = 1.0,
) -> PaperComment:
    last_seen: PaperComment | None = None
    for attempt in range(attempts):
        comment = fetch_comment_by_id(api_key, comment_id, paper_id=paper_id)
        last_seen = comment
        if comment.has_upvoted is expected:
            return comment
        if attempt < attempts - 1:
            time.sleep(delay_seconds)
    raise AssertionError(
        f"Comment '{comment_id}' did not reach has_upvoted={expected}. "
        f"Last observed value: {last_seen.has_upvoted if last_seen else 'unknown'}."
    )


def load_saved_assistant_context() -> AssistantContext | None:
    from alphaxiv.cli.helpers import load_assistant_context

    return load_assistant_context()


async def _fetch_folders(api_key: str) -> list[Folder]:
    async with AlphaXivClient(api_key=api_key) as client:
        return await client.folders.list()


def fetch_folders(api_key: str) -> list[Folder]:
    return asyncio.run(_fetch_folders(api_key))


async def _fetch_paper_group_id(api_key: str, paper_id: str) -> str:
    async with AlphaXivClient(api_key=api_key) as client:
        resolved = await client.papers.resolve(paper_id)
        if not resolved.group_id:
            raise AssertionError(f"No paper group id was available for '{paper_id}'.")
        return resolved.group_id


def fetch_paper_group_id(api_key: str, paper_id: str = SMOKE_PAPER_ID) -> str:
    return asyncio.run(_fetch_paper_group_id(api_key, paper_id))


def find_folder_membership_target(
    api_key: str,
    *,
    paper_id: str = SMOKE_PAPER_ID,
) -> tuple[Folder, bool]:
    paper_group_id = fetch_paper_group_id(api_key, paper_id)
    folders = fetch_folders(api_key)
    if not folders:
        raise AssertionError("No live alphaXiv folders were returned.")

    without_paper = [
        folder for folder in folders if not folder.contains_paper_group_id(paper_group_id)
    ]
    if without_paper:
        return without_paper[0], False
    return folders[0], True


def wait_for_folder_membership_state(
    api_key: str,
    folder_selector: str,
    paper_group_id: str,
    expected: bool,
    *,
    attempts: int = 5,
    delay_seconds: float = 1.0,
) -> Folder:
    last_seen: Folder | None = None
    for attempt in range(attempts):
        folders = fetch_folders(api_key)
        folder = next(
            (
                item
                for item in folders
                if item.id == folder_selector or item.name.casefold() == folder_selector.casefold()
            ),
            None,
        )
        if folder is None:
            raise AssertionError(f"Folder '{folder_selector}' was not found in live alphaXiv data.")
        last_seen = folder
        has_paper = folder.contains_paper_group_id(paper_group_id)
        if has_paper is expected:
            return folder
        if attempt < attempts - 1:
            time.sleep(delay_seconds)
    raise AssertionError(
        f"Folder '{folder_selector}' did not reach contains_paper_group_id={expected} for "
        f"{paper_group_id}. Last observed value: "
        f"{last_seen.contains_paper_group_id(paper_group_id) if last_seen else 'unknown'}."
    )
