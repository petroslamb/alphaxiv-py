"""Homepage search and feed CLI commands."""

from __future__ import annotations

import click
from rich.table import Table

from .._explore import FEED_INTERVALS, FEED_MENU_CATEGORIES, FEED_SORTS
from ..types import (
    ExploreFilterOptions,
    FeedCard,
    HomepageSearchResults,
    OrganizationResult,
    SearchResult,
)
from .helpers import console, make_client, run_async

feed = click.Group("feed", help="Homepage feed commands.")


def fetch_homepage_search(query: str) -> HomepageSearchResults:
    async def _search() -> HomepageSearchResults:
        async with make_client() as client:
            return await client.search.homepage(query)

    return run_async(_search())


def fetch_paper_search(query: str) -> list[SearchResult]:
    async def _search() -> list[SearchResult]:
        async with make_client() as client:
            return await client.search.papers(query)

    return run_async(_search())


def fetch_organization_search(query: str) -> list[OrganizationResult]:
    async def _search() -> list[OrganizationResult]:
        async with make_client() as client:
            return await client.search.organizations(query)

    return run_async(_search())


def fetch_topic_search(query: str) -> list[str]:
    async def _search() -> list[str]:
        async with make_client() as client:
            return await client.search.closest_topics(query)

    return run_async(_search())


def fetch_feed_cards(
    *,
    sort: str,
    organizations: tuple[str, ...],
    menu_categories: tuple[str, ...],
    categories: tuple[str, ...],
    subcategories: tuple[str, ...],
    custom_categories: tuple[str, ...],
    source: str | None,
    interval: str | None,
    limit: int | None,
) -> list[FeedCard]:
    async def _feed() -> list[FeedCard]:
        async with make_client() as client:
            return await client.explore.feed(
                sort=sort,
                organizations=organizations,
                menu_categories=menu_categories,
                categories=categories,
                subcategories=subcategories,
                custom_categories=custom_categories,
                source=source,
                interval=interval,
                limit=limit,
            )

    return run_async(_feed())


def fetch_filter_options() -> ExploreFilterOptions:
    async def _filters() -> ExploreFilterOptions:
        async with make_client() as client:
            return await client.explore.filter_options()

    return run_async(_filters())


def _render_papers_table(query: str, search_results: HomepageSearchResults) -> None:
    table = Table(title=f"Search Results for: {query}")
    table.add_column("Paper ID")
    table.add_column("Title")
    table.add_column("Link")
    for result in search_results.papers:
        table.add_row(result.paper_id, result.title, f"https://www.alphaxiv.org{result.link}")
    console.print(table)


def _render_paper_results_table(query: str, results: list[SearchResult]) -> None:
    table = Table(title=f"Paper Search Results for: {query}")
    table.add_column("Paper ID")
    table.add_column("Title")
    table.add_column("Link")
    for result in results:
        table.add_row(result.paper_id, result.title, f"https://www.alphaxiv.org{result.link}")
    console.print(table)


def _render_topics_table(topics: list[str]) -> None:
    table = Table(title="Suggested Topics")
    table.add_column("Topic")
    for topic in topics:
        table.add_row(topic)
    console.print(table)


def _render_organizations_table(organizations: list[OrganizationResult], title: str = "Organizations") -> None:
    table = Table(title=title)
    table.add_column("Name")
    table.add_column("Slug")
    for organization in organizations:
        table.add_row(organization.name, organization.slug or "-")
    console.print(table)


@feed.command("list")
@click.option(
    "--sort",
    type=click.Choice([item.lower() for item in FEED_SORTS], case_sensitive=False),
    default="hot",
    show_default=True,
)
@click.option("--organization", "organizations", multiple=True, help="Filter by organization name.")
@click.option(
    "--menu-category",
    "menu_categories",
    multiple=True,
    help="Filter by homepage menu category, e.g. 'Computer Science'.",
)
@click.option("--category", "categories", multiple=True, help="Filter by category topic slug.")
@click.option(
    "--subcategory",
    "subcategories",
    multiple=True,
    help="Filter by subcategory topic slug.",
)
@click.option(
    "--custom-category",
    "custom_categories",
    multiple=True,
    help="Filter by custom category topic slug.",
)
@click.option(
    "--source",
    type=click.Choice(["github", "twitter"], case_sensitive=False),
    default=None,
    help="Filter by feed source.",
)
@click.option(
    "--interval",
    type=click.Choice(["3-days", "7-days", "30-days", "90-days", "all-time"], case_sensitive=False),
    default=None,
    help="Filter by publication-date interval.",
)
@click.option("--limit", type=int, default=10, show_default=True)
def list_feed(
    sort: str,
    organizations: tuple[str, ...],
    menu_categories: tuple[str, ...],
    categories: tuple[str, ...],
    subcategories: tuple[str, ...],
    custom_categories: tuple[str, ...],
    source: str | None,
    interval: str | None,
    limit: int,
) -> None:
    """List homepage feed cards."""
    source_value = None
    if source == "github":
        source_value = "GitHub"
    elif source == "twitter":
        source_value = "Twitter (X)"

    interval_value = interval.replace("-", " ").title() if interval else None
    cards = fetch_feed_cards(
        sort=sort,
        organizations=organizations,
        menu_categories=menu_categories,
        categories=categories,
        subcategories=subcategories,
        custom_categories=custom_categories,
        source=source_value,
        interval=interval_value,
        limit=limit,
    )

    table = Table(title="alphaXiv Feed")
    table.add_column("Paper ID")
    table.add_column("Title")
    table.add_column("Date")
    table.add_column("Upvotes")
    table.add_column("Visits")
    table.add_column("GitHub")
    table.add_column("X Likes")
    table.add_column("Tags")
    for card in cards:
        publication_date = card.publication_date.date().isoformat() if card.publication_date else "-"
        tags = ", ".join(card.topics[:3]) or "-"
        github_stars = str(card.github_stars) if card.github_stars is not None else "-"
        x_likes = str(card.x_likes) if card.x_likes else "-"
        table.add_row(
            card.paper_id,
            card.title,
            publication_date,
            str(card.upvotes),
            str(card.visits),
            github_stars,
            x_likes,
            tags,
        )
    console.print(table)


@feed.command("filters")
def show_filter_options() -> None:
    """Show known homepage feed filter options."""
    options = fetch_filter_options()

    sorts_table = Table(title="Feed Sorts")
    sorts_table.add_column("Value")
    for item in options.sorts:
        sorts_table.add_row(item)
    console.print(sorts_table)

    categories_table = Table(title="Homepage Menu Categories")
    categories_table.add_column("Value")
    for item in options.menu_categories:
        categories_table.add_row(item)
    console.print(categories_table)

    interval_table = Table(title="Publication Date Filters")
    interval_table.add_column("Value")
    for item in options.intervals:
        interval_table.add_row(item)
    console.print(interval_table)

    source_table = Table(title="Feed Sources")
    source_table.add_column("Value")
    for item in options.sources:
        source_table.add_row(item)
    console.print(source_table)

    organizations_table = Table(title="Top Organizations")
    organizations_table.add_column("Name")
    organizations_table.add_column("Slug")
    for organization in options.organizations:
        organizations_table.add_row(organization.name, organization.slug or "-")
    console.print(organizations_table)


def register_explore_commands(cli):
    @cli.command("search")
    @click.argument("query")
    def search(query: str) -> None:
        """Search alphaXiv homepage papers, topics, and organizations."""
        results = fetch_homepage_search(query)
        _render_papers_table(query, results)
        if results.topics:
            _render_topics_table(results.topics)
        if results.organizations:
            _render_organizations_table(results.organizations)

    @cli.command("search-papers")
    @click.argument("query")
    def search_papers(query: str) -> None:
        """Search only the public paper endpoint used by the homepage."""
        results = fetch_paper_search(query)
        _render_paper_results_table(query, results)

    @cli.command("search-organizations")
    @click.argument("query")
    def search_organizations(query: str) -> None:
        """Search only the public organization endpoint used by the homepage."""
        results = fetch_organization_search(query)
        _render_organizations_table(results, title=f"Organization Results for: {query}")

    @cli.command("search-topics")
    @click.argument("query")
    def search_topics(query: str) -> None:
        """Search only the public closest-topic endpoint used by the homepage."""
        results = fetch_topic_search(query)
        _render_topics_table(results)
