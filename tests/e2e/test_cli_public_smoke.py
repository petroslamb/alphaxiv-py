from __future__ import annotations

from pathlib import Path

import pytest
from tests.e2e.helpers import SMOKE_PAPER_ID, assert_cli_ok, invoke_cli, require_live_smoke

pytestmark = pytest.mark.e2e


def test_cli_public_search_and_feed_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    require_live_smoke()

    search_result = invoke_cli(
        cli_runner,
        ["search", "papers", "attention is all you need"],
        env=isolated_cli_env,
    )
    assert_cli_ok(search_result, "search", "papers", "attention is all you need")
    assert "Paper Search Results for: attention is all you need" in search_result.output
    assert SMOKE_PAPER_ID in search_result.output

    filters_result = invoke_cli(
        cli_runner,
        ["feed", "filters"],
        env=isolated_cli_env,
    )
    assert_cli_ok(filters_result, "feed", "filters")
    assert "Feed Sorts" in filters_result.output
    assert "Feed Sources" in filters_result.output

    hot_feed_result = invoke_cli(
        cli_runner,
        ["feed", "list", "--sort", "hot", "--limit", "1"],
        env=isolated_cli_env,
    )
    assert_cli_ok(hot_feed_result, "feed", "list", "--sort", "hot", "--limit", "1")
    assert "alphaXiv Feed" in hot_feed_result.output

    github_feed_result = invoke_cli(
        cli_runner,
        ["feed", "list", "--sort", "most-stars", "--source", "github", "--limit", "1"],
        env=isolated_cli_env,
    )
    assert_cli_ok(
        github_feed_result,
        "feed",
        "list",
        "--sort",
        "most-stars",
        "--source",
        "github",
        "--limit",
        "1",
    )
    assert "alphaXiv Feed" in github_feed_result.output

    filter_search_result = invoke_cli(
        cli_runner,
        ["feed", "filters", "search", "agentic"],
        env=isolated_cli_env,
    )
    assert_cli_ok(filter_search_result, "feed", "filters", "search", "agentic")
    assert "Feed Filter Topics for: agentic" in filter_search_result.output


def test_cli_public_context_and_paper_reads_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
    tmp_path: Path,
) -> None:
    require_live_smoke()

    context_use = invoke_cli(
        cli_runner,
        ["context", "use", "paper", SMOKE_PAPER_ID],
        env=isolated_cli_env,
    )
    assert_cli_ok(context_use, "context", "use", "paper", SMOKE_PAPER_ID)
    assert "Current paper set" in context_use.output

    paper_show = invoke_cli(cli_runner, ["paper", "show"], env=isolated_cli_env)
    assert_cli_ok(paper_show, "paper", "show")
    assert "Attention Is All You Need" in paper_show.output
    assert "1706.03762v7" in paper_show.output

    overview_status = invoke_cli(
        cli_runner,
        ["paper", "overview-status", SMOKE_PAPER_ID],
        env=isolated_cli_env,
    )
    assert_cli_ok(overview_status, "paper", "overview-status", SMOKE_PAPER_ID)
    assert "Overview Status" in overview_status.output
    assert "en" in overview_status.output

    full_text = invoke_cli(
        cli_runner,
        ["paper", "text", SMOKE_PAPER_ID, "--page", "1"],
        env=isolated_cli_env,
    )
    assert_cli_ok(full_text, "paper", "text", SMOKE_PAPER_ID, "--page", "1")
    assert "Full Text" in full_text.output
    assert "Page 1" in full_text.output

    resources = invoke_cli(
        cli_runner,
        ["paper", "resources", SMOKE_PAPER_ID, "--bibtex"],
        env=isolated_cli_env,
    )
    assert_cli_ok(resources, "paper", "resources", SMOKE_PAPER_ID, "--bibtex")
    assert "@article" in resources.output.lower()

    pdf_url = invoke_cli(
        cli_runner,
        ["paper", "pdf", "url", SMOKE_PAPER_ID],
        env=isolated_cli_env,
    )
    assert_cli_ok(pdf_url, "paper", "pdf", "url", SMOKE_PAPER_ID)
    assert "fetcher.alphaxiv.org" in pdf_url.output

    pdf_path = tmp_path / "attention.pdf"
    download = invoke_cli(
        cli_runner,
        ["paper", "pdf", "download", SMOKE_PAPER_ID, str(pdf_path)],
        env=isolated_cli_env,
    )
    assert_cli_ok(download, "paper", "pdf", "download", SMOKE_PAPER_ID, str(pdf_path))
    assert "Downloaded PDF to:" in download.output
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_cli_public_comments_and_similar_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    require_live_smoke()

    comments_result = invoke_cli(
        cli_runner,
        ["paper", "comments", "list", SMOKE_PAPER_ID],
        env=isolated_cli_env,
    )
    assert_cli_ok(comments_result, "paper", "comments", "list", SMOKE_PAPER_ID)
    assert f"Comments for {SMOKE_PAPER_ID}" in comments_result.output

    similar_result = invoke_cli(
        cli_runner,
        ["paper", "similar", SMOKE_PAPER_ID, "--limit", "5"],
        env=isolated_cli_env,
    )
    assert_cli_ok(similar_result, "paper", "similar", SMOKE_PAPER_ID, "--limit", "5")
    assert "Similar Papers" in similar_result.output
