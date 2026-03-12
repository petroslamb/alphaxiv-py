"""Search API implementation."""

from __future__ import annotations

import asyncio

from ._core import BASE_API_URL, ClientCore
from .types import HomepageSearchResults, OrganizationResult, SearchResult


class SearchAPI:
    """Search-related alphaXiv operations."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core

    async def papers(self, query: str, include_private: bool = False) -> list[SearchResult]:
        payload = await self._core.get_json(
            f"{BASE_API_URL}/search/v2/paper/fast",
            params={"q": query, "includePrivate": str(include_private).lower()},
        )
        if not isinstance(payload, list):
            return []
        return [SearchResult.from_payload(item) for item in payload if isinstance(item, dict)]

    async def organizations(self, query: str) -> list[OrganizationResult]:
        payload = await self._core.get_json(
            f"{BASE_API_URL}/organizations/v2/search",
            params={"q": query},
        )
        if not isinstance(payload, list):
            return []
        return [OrganizationResult.from_payload(item) for item in payload if isinstance(item, dict)]

    async def closest_topics(self, query: str) -> list[str]:
        payload = await self._core.get_json(
            f"{BASE_API_URL}/v1/search/closest-topic",
            params={"input": query},
        )
        if not isinstance(payload, dict):
            return []
        return [str(item) for item in payload.get("data") or []]

    async def homepage(self, query: str, include_private: bool = False) -> HomepageSearchResults:
        papers, organizations, topics = await asyncio.gather(
            self.papers(query, include_private=include_private),
            self.organizations(query),
            self.closest_topics(query),
        )
        return HomepageSearchResults(
            query=query,
            papers=papers,
            organizations=organizations,
            topics=topics,
            raw={
                "papers": [item.raw for item in papers],
                "organizations": [item.raw for item in organizations],
                "topics": topics,
            },
        )
