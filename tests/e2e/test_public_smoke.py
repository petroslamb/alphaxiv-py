from __future__ import annotations

import pytest
from tests.e2e.helpers import require_live_smoke

from alphaxiv import AlphaXivClient

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_public_search_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        results = await client.search.papers("attention is all you need")
    assert results
    assert any("attention" in result.title.lower() for result in results)


@pytest.mark.asyncio
async def test_public_paper_fetch_smoke() -> None:
    require_live_smoke()
    async with AlphaXivClient() as client:
        paper = await client.papers.get("1706.03762")
    assert paper.resolved.canonical_id is not None
    assert "attention" in paper.version.title.lower()


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
