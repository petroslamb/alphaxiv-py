from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Iterable
from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from alphaxiv import AlphaXivClient
from alphaxiv.alphaxiv_cli import cli
from alphaxiv.auth import ALPHAXIV_API_KEY_ENV
from alphaxiv.types import AssistantContext, PaperComment

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
