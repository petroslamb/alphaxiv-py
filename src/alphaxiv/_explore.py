"""Homepage explore/feed APIs."""

from __future__ import annotations

import ast
import json
import re
from datetime import datetime, timedelta, timezone

from ._core import BASE_API_URL, BASE_WEB_URL, ClientCore
from .exceptions import APIError
from .types import ExploreFilterOptions, FeedCard, OrganizationResult

FEED_SORTS = ("Hot", "Likes")
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

_REF_ASSIGN_RE = re.compile(r"\$R\[\d+\]=")
_REF_RE = re.compile(r"\$R\[(\d+)\]")
_STRING_RE = re.compile(r'("(?:[^"\\]|\\.)*")')
_KEY_RE = re.compile(r'([\[{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)')

_INTERVAL_TO_DAYS = {
    "3 days": 3,
    "7 days": 7,
    "30 days": 30,
    "90 days": 90,
    "all time": None,
}
_MENU_CATEGORY_TO_TOPICS = {
    "ai & machine learning": {"artificial-intelligence", "machine-learning"},
    "computer science": {"computer-science"},
    "mathematics": {"mathematics"},
    "physics": {"physics"},
    "statistics": {"statistics"},
    "electrical engineering": {"electrical-engineering"},
    "economics": {"economics"},
}


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _normalize_sort(value: str | None) -> str:
    if not value:
        return "Hot"
    normalized = value.strip().lower()
    if normalized not in {"hot", "likes"}:
        raise ValueError(f"Unsupported feed sort '{value}'. Expected Hot or Likes.")
    return normalized.title()


def _normalize_source(value: str | None) -> str | None:
    if not value:
        return None
    normalized = _normalize_token(value)
    if normalized == "github":
        return "GitHub"
    if normalized in {"twitter-x", "twitter"}:
        return "Twitter (X)"
    raise ValueError(f"Unsupported feed source '{value}'. Expected GitHub or Twitter (X).")


def _normalize_interval(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.replace("-", " ").strip().lower()
    if normalized not in _INTERVAL_TO_DAYS:
        raise ValueError(
            f"Unsupported interval '{value}'. Expected one of: {', '.join(FEED_INTERVALS)}."
        )
    for option in FEED_INTERVALS:
        if option.lower() == normalized:
            return option
    return None


def _extract_balanced(text: str, start: int, open_char: str, close_char: str) -> str:
    in_string = False
    escaped = False
    depth = 0
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == open_char:
            depth += 1
            continue
        if char == close_char:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ValueError("Could not find balanced serialized payload.")


def _to_python_literal(serialized: str) -> str:
    text = _REF_ASSIGN_RE.sub("", serialized)
    text = _REF_RE.sub(r"\1", text)

    parts = _STRING_RE.split(text)
    for index in range(0, len(parts), 2):
        part = parts[index]
        part = part.replace("!0", "True").replace("!1", "False").replace("void 0", "None")
        part = re.sub(r"\btrue\b", "True", part)
        part = re.sub(r"\bfalse\b", "False", part)
        part = re.sub(r"\bnull\b", "None", part)
        parts[index] = _KEY_RE.sub(r'\1"\2"\3', part)
    return "".join(parts)


def _extract_trending_payload(html: str) -> list[dict[str, object]]:
    marker = "trendingPapers:"
    start = html.find(marker)
    if start == -1:
        raise ValueError("Could not find the explore feed payload in the page HTML.")

    assign_index = html.find("=", start)
    if assign_index == -1:
        raise ValueError("Could not find the explore feed payload assignment in the page HTML.")

    array_start = html.find("[", assign_index)
    if array_start == -1:
        raise ValueError("Could not find the explore feed payload array in the page HTML.")

    serialized = _extract_balanced(html, array_start, "[", "]")
    python_literal = _to_python_literal(serialized)
    payload = ast.literal_eval(python_literal)
    if not isinstance(payload, list):
        raise ValueError("Explore feed payload was not a list.")
    return [item for item in payload if isinstance(item, dict)]


def _matches_topics(card: FeedCard, filters: tuple[str, ...]) -> bool:
    if not filters:
        return True
    available = {_normalize_token(topic) for topic in card.topics}
    expected = {_normalize_token(item) for item in filters}
    return not expected.isdisjoint(available)


def _matches_menu_categories(card: FeedCard, filters: tuple[str, ...]) -> bool:
    if not filters:
        return True
    available = {_normalize_token(topic) for topic in card.topics}
    for item in filters:
        mapped = _MENU_CATEGORY_TO_TOPICS.get(item.strip().lower())
        if not mapped:
            continue
        if available.intersection(mapped):
            return True
    return False


def _matches_organizations(card: FeedCard, filters: tuple[str, ...]) -> bool:
    if not filters:
        return True
    available = {_normalize_token(item) for item in card.organizations}
    expected = {_normalize_token(item) for item in filters}
    return not expected.isdisjoint(available)


def _matches_source(card: FeedCard, source: str | None) -> bool:
    if not source:
        return True
    if source == "GitHub":
        return bool(card.github_url)
    if source == "Twitter (X)":
        return card.x_likes > 0
    return True


def _matches_interval(card: FeedCard, interval: str | None) -> bool:
    if not interval or interval == "All time":
        return True
    days = _INTERVAL_TO_DAYS[interval.lower()]
    if days is None:
        return True
    if card.publication_date is None:
        return False
    now = datetime.now(timezone.utc)
    published = card.publication_date
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    return published >= now - timedelta(days=days)


def _apply_local_filters(
    cards: list[FeedCard],
    *,
    organizations: tuple[str, ...],
    menu_categories: tuple[str, ...],
    categories: tuple[str, ...],
    subcategories: tuple[str, ...],
    custom_categories: tuple[str, ...],
    source: str | None,
    interval: str | None,
) -> list[FeedCard]:
    filtered: list[FeedCard] = []
    topic_filters = categories + subcategories + custom_categories
    for card in cards:
        if not _matches_organizations(card, organizations):
            continue
        if not _matches_menu_categories(card, menu_categories):
            continue
        if not _matches_topics(card, topic_filters):
            continue
        if not _matches_source(card, source):
            continue
        if not _matches_interval(card, interval):
            continue
        filtered.append(card)
    return filtered


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

    async def feed(
        self,
        *,
        sort: str = "Hot",
        organizations: tuple[str, ...] = (),
        menu_categories: tuple[str, ...] = (),
        categories: tuple[str, ...] = (),
        subcategories: tuple[str, ...] = (),
        custom_categories: tuple[str, ...] = (),
        source: str | None = None,
        interval: str | None = None,
        limit: int | None = None,
    ) -> list[FeedCard]:
        canonical_sort = _normalize_sort(sort)
        canonical_source = _normalize_source(source)
        canonical_interval = _normalize_interval(interval)

        params: dict[str, str] = {"sort": canonical_sort}
        if organizations:
            params["organizations"] = json.dumps(list(organizations))
        if canonical_source:
            params["source"] = canonical_source
        if canonical_interval and canonical_interval != "All time":
            params["interval"] = canonical_interval

        html = await self._core.get_text(BASE_WEB_URL, params=params)
        try:
            payload = _extract_trending_payload(html)
        except (SyntaxError, ValueError) as exc:
            raise APIError(
                "Could not parse the alphaXiv explore feed payload.",
                url=BASE_WEB_URL,
                response_text=html[:1000],
            ) from exc

        cards = [FeedCard.from_payload(item) for item in payload]
        filtered = _apply_local_filters(
            cards,
            organizations=organizations,
            menu_categories=menu_categories,
            categories=categories,
            subcategories=subcategories,
            custom_categories=custom_categories,
            source=canonical_source,
            interval=canonical_interval,
        )
        if limit is not None:
            return filtered[:limit]
        return filtered
