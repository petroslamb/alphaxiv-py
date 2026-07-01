from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.e2e.helpers import SMOKE_PAPER_ID, assert_cli_ok, invoke_cli, require_live_smoke

pytestmark = pytest.mark.e2e

SIDECAR_SMOKE_VERSION_ID = "019e057a-354c-7480-afd1-a79e18674c1e"


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

    search_json = invoke_cli(
        cli_runner,
        ["search", "papers", "attention is all you need", "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(search_json, "search", "papers", "attention is all you need", "--json")
    assert '"paper_id": "1706.03762"' in search_json.output

    rich_search_json = invoke_cli(
        cli_runner,
        ["search", "papers", "attention", "--rich", "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(rich_search_json, "search", "papers", "attention", "--rich", "--json")
    rich_search_payload = json.loads(rich_search_json.output)
    assert rich_search_payload["papers"]
    assert rich_search_payload["papers"][0]["title"]

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

    hot_feed_json = invoke_cli(
        cli_runner,
        ["feed", "list", "--sort", "hot", "--limit", "1", "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(
        hot_feed_json,
        "feed",
        "list",
        "--sort",
        "hot",
        "--limit",
        "1",
        "--json",
    )
    hot_feed_payload = json.loads(hot_feed_json.output)
    assert hot_feed_payload["filters"]["sort"] == "hot"
    assert hot_feed_payload["cards"]

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

    filter_search_json = invoke_cli(
        cli_runner,
        ["feed", "filters", "search", "agentic", "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(filter_search_json, "feed", "filters", "search", "agentic", "--json")
    assert '"topics": [' in filter_search_json.output


def test_cli_public_events_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    require_live_smoke()

    events_json = invoke_cli(
        cli_runner,
        ["events", "list", "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(events_json, "events", "list", "--json")
    events_payload = json.loads(events_json.output)
    assert events_payload["events"]
    assert events_payload["events"][0]["title"]


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

    overview_status_json = invoke_cli(
        cli_runner,
        ["paper", "overview-status", SMOKE_PAPER_ID, "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(overview_status_json, "paper", "overview-status", SMOKE_PAPER_ID, "--json")
    assert '"version_id"' in overview_status_json.output

    preview_json = invoke_cli(
        cli_runner,
        ["paper", "preview", SMOKE_PAPER_ID, "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(preview_json, "paper", "preview", SMOKE_PAPER_ID, "--json")
    preview_payload = json.loads(preview_json.output)
    assert preview_payload["version_id"]
    assert preview_payload["title"]

    figures_json = invoke_cli(
        cli_runner,
        ["paper", "figures", SMOKE_PAPER_ID, "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(figures_json, "paper", "figures", SMOKE_PAPER_ID, "--json")
    figures_payload = json.loads(figures_json.output)
    assert figures_payload["paper_group_id"]
    assert isinstance(figures_payload["figures"], list)

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
    resources_output = resources.output.lower()
    assert resources_output.startswith("@")
    assert "attention is all you need" in resources_output
    assert "1706.03762" in resources_output
    assert "arxiv" in resources_output

    pdf_url = invoke_cli(
        cli_runner,
        ["paper", "pdf", "url", SMOKE_PAPER_ID],
        env=isolated_cli_env,
    )
    assert_cli_ok(pdf_url, "paper", "pdf", "url", SMOKE_PAPER_ID)
    assert "alphaxiv.org" in pdf_url.output
    assert pdf_url.output.strip().endswith(".pdf")

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


def test_cli_public_paper_sidecar_smoke(
    cli_runner,
    isolated_cli_env: dict[str, str],
) -> None:
    require_live_smoke()

    detection_json = invoke_cli(
        cli_runner,
        ["paper", "ai-detection", SIDECAR_SMOKE_VERSION_ID, "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(detection_json, "paper", "ai-detection", SIDECAR_SMOKE_VERSION_ID, "--json")
    detection_payload = json.loads(detection_json.output)
    assert detection_payload["state"]

    links_json = invoke_cli(
        cli_runner,
        ["paper", "model-links", SIDECAR_SMOKE_VERSION_ID, "--json"],
        env=isolated_cli_env,
    )
    assert_cli_ok(links_json, "paper", "model-links", SIDECAR_SMOKE_VERSION_ID, "--json")
    links_payload = json.loads(links_json.output)
    assert links_payload["state"]


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
