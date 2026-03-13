"""Homepage search and feed APIs."""

from __future__ import annotations

import asyncio
import json
import re

from ._core import BASE_API_URL, ClientCore
from .types import ExploreFilterOptions, FeedCard, FeedFilterSearchResults, OrganizationResult

FEED_SORTS = ("Hot", "Likes", "GitHub", "Twitter (X)")
FEED_MENU_CATEGORIES = (
    "AI & Machine Learning",
    "Computer Science",
    "Mathematics",
    "Physics",
    "Statistics",
    "Electrical Engineering",
    "Economics",
)
FEED_INTERVALS = ("3 Days", "7 Days", "30 Days", "90 Days", "All time")
FEED_SOURCES = ("GitHub", "Twitter (X)")


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _normalize_sort(value: str | None) -> tuple[str, str | None]:
    if not value:
        return "Hot", None

    normalized = _normalize_token(value)
    if normalized == "hot":
        return "Hot", None
    if normalized == "likes":
        return "Likes", None
    if normalized in {"github", "most-stars", "stars"}:
        return "GitHub", "GitHub"
    if normalized in {"twitter", "twitter-x", "most-twitter-likes", "most-twitter-x-likes"}:
        return "Twitter (X)", "Twitter (X)"

    raise ValueError(
        "Unsupported feed sort "
        f"'{value}'. Expected one of: hot, likes, github, twitter, most-stars, "
        "most-twitter-likes."
    )


def _normalize_source(value: str | None) -> str | None:
    if not value:
        return None

    normalized = _normalize_token(value)
    if normalized == "github":
        return "GitHub"
    if normalized in {"twitter-x", "twitter"}:
        return "Twitter (X)"

    raise ValueError(f"Unsupported feed source '{value}'. Expected GitHub or Twitter (X).")


def _normalize_interval(value: str | None) -> str:
    if not value:
        return "All time"

    normalized = value.replace("-", " ").strip().lower()
    for option in FEED_INTERVALS:
        if option.lower() == normalized:
            return option

    raise ValueError(
        f"Unsupported interval '{value}'. Expected one of: {', '.join(FEED_INTERVALS)}."
    )


def _normalize_menu_category(value: str) -> str:
    return _normalize_token(value.strip())


def _normalize_filter_slug(value: str) -> str:
    return _normalize_token(value.strip())


def _normalize_raw_topic(value: str) -> str:
    stripped = value.strip()
    if re.fullmatch(r"[A-Za-z]+\.[A-Za-z0-9-]+", stripped):
        return stripped
    return _normalize_token(stripped)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


class ExploreAPI:
    """alphaXiv homepage explore/feed operations."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core

    async def top_organizations(self) -> list[OrganizationResult]:
        payload = await self._core.get_json(f"{BASE_API_URL}/organizations/v2/top")
        if not isinstance(payload, list):
            return []
        return [OrganizationResult.from_payload(item) for item in payload if isinstance(item, dict)]

    async def filter_options(self) -> ExploreFilterOptions:
        organizations = await self.top_organizations()
        return ExploreFilterOptions(
            sorts=list(FEED_SORTS),
            menu_categories=list(FEED_MENU_CATEGORIES),
            intervals=list(FEED_INTERVALS),
            sources=list(FEED_SOURCES),
            organizations=organizations,
            raw={"organizations": [item.raw for item in organizations]},
        )

    async def search_filters(self, query: str) -> FeedFilterSearchResults:
        topic_payload, organization_payload = await asyncio.gather(
            self._core.get_json(
                f"{BASE_API_URL}/v1/search/closest-topic",
                params={"input": query},
            ),
            self._core.get_json(
                f"{BASE_API_URL}/organizations/v2/search",
                params={"q": query},
            ),
        )

        topics: list[str] = []
        if isinstance(topic_payload, dict):
            data = topic_payload.get("data")
            if isinstance(data, list):
                topics = [str(item) for item in data if isinstance(item, str)]

        organizations: list[OrganizationResult] = []
        if isinstance(organization_payload, list):
            organizations = [
                OrganizationResult.from_payload(item)
                for item in organization_payload
                if isinstance(item, dict)
            ]

        return FeedFilterSearchResults(
            query=query,
            topics=topics,
            organizations=organizations,
            raw={
                "topics": topic_payload,
                "organizations": organization_payload,
            },
        )

    async def feed(
        self,
        *,
        sort: str = "Hot",
        organizations: tuple[str, ...] = (),
        menu_categories: tuple[str, ...] = (),
        categories: tuple[str, ...] = (),
        subcategories: tuple[str, ...] = (),
        custom_categories: tuple[str, ...] = (),
        topics: tuple[str, ...] = (),
        source: str | None = None,
        interval: str | None = None,
        limit: int | None = None,
    ) -> list[FeedCard]:
        canonical_sort, implied_source = _normalize_sort(sort)
        canonical_source = _normalize_source(source)
        if implied_source:
            if canonical_source and canonical_source != implied_source:
                raise ValueError(
                    f"Feed sort '{sort}' requires source '{implied_source}', not '{canonical_source}'."
                )
            canonical_source = implied_source

        page_size = limit or 20
        params: dict[str, str | int] = {
            "pageNum": 0,
            "pageSize": page_size,
            "sort": canonical_sort,
            "interval": _normalize_interval(interval),
        }

        if organizations:
            params["organizations"] = json.dumps([item.strip() for item in organizations if item.strip()])

        category_filters = _dedupe(
            [_normalize_menu_category(item) for item in menu_categories]
            + [_normalize_filter_slug(item) for item in categories]
        )
        if category_filters:
            params["categories"] = json.dumps(category_filters)

        subcategory_filters = _dedupe([_normalize_filter_slug(item) for item in subcategories])
        if subcategory_filters:
            params["subcategories"] = json.dumps(subcategory_filters)

        custom_category_filters = _dedupe(
            [_normalize_filter_slug(item) for item in custom_categories]
        )
        if custom_category_filters:
            params["customCategories"] = json.dumps(custom_category_filters)

        topic_filters = _dedupe([_normalize_raw_topic(item) for item in topics])
        if topic_filters:
            params["topics"] = json.dumps(topic_filters)

        if canonical_source:
            params["source"] = canonical_source

        payload = await self._core.get_json(f"{BASE_API_URL}/papers/v3/feed", params=params)
        papers_payload: list[dict[str, object]] = []
        if isinstance(payload, dict):
            papers = payload.get("papers")
            if isinstance(papers, list):
                papers_payload = [item for item in papers if isinstance(item, dict)]
        elif isinstance(payload, list):
            papers_payload = [item for item in payload if isinstance(item, dict)]

        cards = [FeedCard.from_payload(item) for item in papers_payload]
        if limit is not None:
            return cards[:limit]
        return cards
