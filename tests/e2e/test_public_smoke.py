from __future__ import annotations

import pytest
from tests.e2e.helpers import require_live_smoke

from alphaxiv import AlphaXivClient

pytestmark = pytest.mark.e2e

SIDECAR_SMOKE_VERSION_ID = "019e057a-354c-7480-afd1-a79e18674c1e"


@pytest.mark.asyncio
async def test_public_search_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        results = await client.search.papers("attention is all you need")
        rich_results = await client.search.papers_rich("attention")
    assert results
    assert any("attention" in result.title.lower() for result in results)
    assert rich_results
    assert any("attention" in result.title.lower() for result in rich_results)


@pytest.mark.asyncio
async def test_public_events_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        events = await client.events.list()
    assert events
    assert all(event.title for event in events)


@pytest.mark.asyncio
async def test_public_paper_fetch_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        paper = await client.papers.get("1706.03762")
        preview = await client.papers.preview("1706.03762")
        figures = await client.papers.figures("1706.03762")
    assert paper.resolved.canonical_id is not None
    assert "attention" in paper.version.title.lower()
    assert preview.version_id
    assert preview.title
    assert figures.paper_group_id
    assert isinstance(figures.figures, list)


@pytest.mark.asyncio
async def test_public_paper_sidecar_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        detection = await client.papers.ai_detection(SIDECAR_SMOKE_VERSION_ID)
        links = await client.papers.model_links(SIDECAR_SMOKE_VERSION_ID)
    assert detection is not None
    assert detection.state
    assert links is not None
    assert links.state


@pytest.mark.asyncio
async def test_public_overview_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        overview = await client.papers.overview("1706.03762")
    assert overview.title
    assert overview.overview_markdown


@pytest.mark.asyncio
async def test_public_overview_status_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        status = await client.papers.overview_status("1706.03762")
    assert status.state
    assert "en" in status.translations


@pytest.mark.asyncio
async def test_public_full_text_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        full_text = await client.papers.full_text("1706.03762")
    assert full_text.page_count > 0
    assert full_text.pages[0].text
