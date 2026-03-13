"""Homepage search and feed CLI commands."""

from __future__ import annotations

import click
from rich.table import Table

from ..types import (
    ExploreFilterOptions,
    FeedCard,
    FeedFilterSearchResults,
    HomepageSearchResults,
    OrganizationResult,
    SearchResult,
)
from .grouped import WrappedHelpGroup
from .helpers import console, make_client, run_async

search = WrappedHelpGroup(
    "search",
    help=(
        "Search public alphaXiv paper, topic, and organization endpoints.\n\n"
        "Examples:\n"
        '  alphaxiv search all "attention is all you need"\n'
        '  alphaxiv search papers "graph neural networks"\n'
        '  alphaxiv search topics "reinforcement learning"'
    ),
)

feed = WrappedHelpGroup(
    "feed",
    help=(
        "Inspect the public alphaXiv homepage feed, discover live filter values, "
        "and list feed cards.\n\n"
        "Examples:\n"
        "  alphaxiv feed filters\n"
        '  alphaxiv feed filters search "agentic"\n'
        "  alphaxiv feed list --topic agentic-frameworks --organization Meta --limit 5\n"
        "  alphaxiv feed list --source github --sort most-stars --limit 5"
    ),
)


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
    topics: tuple[str, ...],
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
                topics=topics,
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


def fetch_feed_filter_search(query: str) -> FeedFilterSearchResults:
    async def _search() -> FeedFilterSearchResults:
        async with make_client() as client:
            return await client.explore.search_filters(query)

    return run_async(_search())


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


def _render_organizations_table(
    organizations: list[OrganizationResult], title: str = "Organizations"
) -> None:
    table = Table(title=title)
    table.add_column("Name")
    table.add_column("Slug")
    for organization in organizations:
        table.add_row(organization.name, organization.slug or "-")
    console.print(table)


def _render_filter_options(options: ExploreFilterOptions) -> None:
    sorts_table = Table(title="Feed Sorts")
    sorts_table.add_column("CLI Sort")
    sorts_table.add_column("Meaning")
    sorts_table.add_row("hot", "Homepage Hot feed")
    sorts_table.add_row("likes", "Most liked feed")
    sorts_table.add_row("most-stars", "GitHub feed sorted by stars")
    sorts_table.add_row("most-twitter-likes", "Twitter feed sorted by X likes")
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
    source_table.add_column("CLI Value")
    source_table.add_column("Website Label")
    source_table.add_row("github", "GitHub")
    source_table.add_row("twitter", "Twitter (X)")
    console.print(source_table)

    organizations_table = Table(title="Top Organizations")
    organizations_table.add_column("Name")
    organizations_table.add_column("Slug")
    for organization in options.organizations:
        organizations_table.add_row(organization.name, organization.slug or "-")
    console.print(organizations_table)

    console.print(
        "Use `alphaxiv feed filters search <query>` to discover live topic and organization filters "
        "the same way the website's filter drawer search box does."
    )


def _render_filter_search(results: FeedFilterSearchResults) -> None:
    if results.topics:
        table = Table(title=f"Feed Filter Topics for: {results.query}")
        table.add_column("Topic")
        table.add_column("Use With")
        for topic in results.topics:
            table.add_row(topic, "--topic")
        console.print(table)

    if results.organizations:
        table = Table(title=f"Feed Filter Organizations for: {results.query}")
        table.add_column("Name")
        table.add_column("Use With")
        for organization in results.organizations:
            table.add_row(organization.name, "--organization")
        console.print(table)

    if not results.topics and not results.organizations:
        console.print(f"No live feed filters found for query: {results.query}")


@search.command("all")
@click.argument("query")
def search_all(query: str) -> None:
    """Search papers, topic suggestions, and organizations in one request."""
    results = fetch_homepage_search(query)
    _render_papers_table(query, results)
    if results.topics:
        _render_topics_table(results.topics)
    if results.organizations:
        _render_organizations_table(results.organizations)


@search.command("papers")
@click.argument("query")
def search_papers(query: str) -> None:
    """Search only the public paper search endpoint used by the homepage."""
    results = fetch_paper_search(query)
    _render_paper_results_table(query, results)


@search.command("organizations")
@click.argument("query")
def search_organizations(query: str) -> None:
    """Search only the public organization search endpoint."""
    results = fetch_organization_search(query)
    _render_organizations_table(results, title=f"Organization Results for: {query}")


@search.command("topics")
@click.argument("query")
def search_topics(query: str) -> None:
    """Return the closest topic suggestions for a natural-language query."""
    results = fetch_topic_search(query)
    _render_topics_table(results)


@feed.command("list")
@click.option(
    "--sort",
    type=click.Choice(
        ["hot", "likes", "github", "twitter", "most-stars", "most-twitter-likes"],
        case_sensitive=False,
    ),
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
    "--topic",
    "topics",
    multiple=True,
    help="Filter by a raw feed topic slug/code from `feed filters search`.",
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
    topics: tuple[str, ...],
    source: str | None,
    interval: str | None,
    limit: int,
) -> None:
    """List public homepage feed cards using alphaXiv-style filters."""
    cards = fetch_feed_cards(
        sort=sort,
        organizations=organizations,
        menu_categories=menu_categories,
        categories=categories,
        subcategories=subcategories,
        custom_categories=custom_categories,
        topics=topics,
        source=source,
        interval=interval,
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
        publication_date = (
            card.publication_date.date().isoformat() if card.publication_date else "-"
        )
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


@click.group(
    "filters",
    cls=WrappedHelpGroup,
    invoke_without_command=True,
    help=(
        "Show the current feed filter groups and search live topic/organization filter values.\n\n"
        "Examples:\n"
        "  alphaxiv feed filters\n"
        '  alphaxiv feed filters search "agentic"'
    ),
)
@click.pass_context
def feed_filters(ctx: click.Context) -> None:
    """Show the current feed sorts, filters, sources, and top organizations."""
    if ctx.invoked_subcommand is None:
        _render_filter_options(fetch_filter_options())


@feed_filters.command("search")
@click.argument("query")
def search_feed_filters(query: str) -> None:
    """Search live topic and organization filters like the website's filter drawer."""
    _render_filter_search(fetch_feed_filter_search(query))


feed.add_command(feed_filters)
