"""Typed data models for alphaxiv-py."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
from typing import Any


def parse_datetime(value: str | None) -> datetime | None:
    """Parse alphaXiv date strings to datetime when possible."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_timestamp_ms(value: int | None) -> datetime | None:
    """Parse Unix timestamps expressed in milliseconds."""
    if not isinstance(value, int):
        return None
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


@dataclass(slots=True)
class SearchResult:
    link: str
    paper_id: str
    title: str
    snippet: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SearchResult":
        return cls(
            link=payload.get("link", ""),
            paper_id=payload.get("paperId", ""),
            title=payload.get("title", ""),
            snippet=payload.get("snippet"),
            raw=payload,
        )


@dataclass(slots=True)
class OrganizationResult:
    id: str
    name: str
    image: str | None
    slug: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "OrganizationResult":
        name = " ".join(str(payload.get("name", "")).split())
        for marker in ("[", "http://", "https://"):
            if marker in name:
                name = name.split(marker, 1)[0].strip()
        for marker in (" However,", " But,"):
            if marker in name:
                name = name.split(marker, 1)[0].strip()
        if len(name) > 100:
            name = f"{name[:97].rstrip()}..."
        return cls(
            id=payload.get("id", ""),
            name=name,
            image=payload.get("image"),
            slug=payload.get("slug"),
            raw=payload,
        )


@dataclass(slots=True)
class HomepageSearchResults:
    query: str
    papers: list[SearchResult]
    organizations: list[OrganizationResult]
    topics: list[str]
    raw: dict[str, Any] = field(repr=False)


@dataclass(slots=True)
class FeedCard:
    group_id: str
    paper_id: str
    canonical_id: str | None
    version_id: str | None
    title: str
    abstract: str
    summary: str | None
    result_highlights: list[str]
    publication_date: datetime | None
    updated_at: datetime | None
    topics: list[str]
    organizations: list[str]
    authors: list[str]
    image_url: str | None
    upvotes: int
    total_votes: int
    x_likes: int
    visits: int
    visits_last_7_days: int
    github_stars: int | None
    github_url: str | None
    raw: dict[str, Any] = field(repr=False)

    @property
    def link(self) -> str:
        return f"/abs/{self.paper_id}"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "FeedCard":
        metrics = payload.get("metrics") or {}
        visits = metrics.get("visits_count") or {}
        summary = payload.get("paper_summary") or {}
        organizations = []
        for item in payload.get("organization_info") or []:
            if isinstance(item, dict) and item.get("name"):
                organizations.append(str(item["name"]))

        return cls(
            group_id=payload.get("paper_group_id") or payload.get("id", ""),
            paper_id=payload.get("universal_paper_id", ""),
            canonical_id=payload.get("canonical_id"),
            version_id=payload.get("version_id"),
            title=payload.get("title", ""),
            abstract=payload.get("abstract", ""),
            summary=summary.get("summary"),
            result_highlights=list(summary.get("results") or []),
            publication_date=parse_datetime(payload.get("publication_date")),
            updated_at=parse_datetime(payload.get("updated_at")),
            topics=list(payload.get("topics") or []),
            organizations=organizations,
            authors=list(payload.get("authors") or []),
            image_url=payload.get("image_url"),
            upvotes=metrics.get("public_total_votes", 0),
            total_votes=metrics.get("total_votes", 0),
            x_likes=metrics.get("x_likes", 0),
            visits=visits.get("all", 0),
            visits_last_7_days=visits.get("last_7_days", 0),
            github_stars=payload.get("github_stars"),
            github_url=payload.get("github_url"),
            raw=payload,
        )


@dataclass(slots=True)
class ExploreFilterOptions:
    sorts: list[str]
    menu_categories: list[str]
    intervals: list[str]
    sources: list[str]
    organizations: list[OrganizationResult]
    raw: dict[str, Any] = field(repr=False)


@dataclass(slots=True)
class ResolvedPaper:
    input_id: str
    versionless_id: str | None
    canonical_id: str | None
    version_id: str | None
    group_id: str | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def preferred_id(self) -> str:
        return self.canonical_id or self.versionless_id or self.version_id or self.input_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_id": self.input_id,
            "versionless_id": self.versionless_id,
            "canonical_id": self.canonical_id,
            "version_id": self.version_id,
            "group_id": self.group_id,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ResolvedPaper":
        return cls(
            input_id=payload.get("input_id", ""),
            versionless_id=payload.get("versionless_id"),
            canonical_id=payload.get("canonical_id"),
            version_id=payload.get("version_id"),
            group_id=payload.get("group_id"),
        )


@dataclass(slots=True)
class AssistantSession:
    id: str
    title: str | None
    newest_message_at: datetime | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AssistantSession":
        newest = payload.get("newestMessage")
        newest_message_at = parse_timestamp_ms(newest) if isinstance(newest, int) else parse_datetime(newest)
        return cls(
            id=payload.get("id", ""),
            title=payload.get("title"),
            newest_message_at=newest_message_at,
            raw=payload,
        )


@dataclass(slots=True)
class AssistantMessage:
    id: str
    message_type: str
    parent_message_id: str | None
    selected_at: datetime | None
    tool_use_id: str | None
    kind: str | None
    content: str | None
    model: str | None
    feedback_type: str | None
    feedback_category: str | None
    feedback_details: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AssistantMessage":
        return cls(
            id=payload.get("id", ""),
            message_type=payload.get("type", ""),
            parent_message_id=payload.get("parentMessageId"),
            selected_at=parse_datetime(payload.get("selectedAt")),
            tool_use_id=payload.get("toolUseId"),
            kind=payload.get("kind"),
            content=payload.get("content"),
            model=payload.get("model"),
            feedback_type=payload.get("feedbackType"),
            feedback_category=payload.get("feedbackCategory"),
            feedback_details=payload.get("feedbackDetails"),
            raw=payload,
        )


@dataclass(slots=True)
class AssistantStreamEvent:
    event_type: str
    index: int | None
    kind: str | None
    delta: str | None
    content: str | None
    tool_use_id: str | None
    error_message: str | None
    raw: dict[str, Any] = field(repr=False)

    @property
    def text(self) -> str:
        return self.delta or self.content or self.error_message or ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AssistantStreamEvent":
        error_message = None
        if payload.get("type") == "error":
            error = payload.get("error")
            if isinstance(error, dict) and error.get("message"):
                error_message = str(error["message"])
            elif payload.get("message"):
                error_message = str(payload["message"])
            elif payload.get("content"):
                error_message = str(payload["content"])

        content = payload.get("content")
        if content is not None and not isinstance(content, str):
            content = json.dumps(content)

        return cls(
            event_type=payload.get("type", "unknown"),
            index=payload.get("index") if isinstance(payload.get("index"), int) else None,
            kind=payload.get("kind"),
            delta=payload.get("delta") if isinstance(payload.get("delta"), str) else None,
            content=content,
            tool_use_id=payload.get("tool_use_id") or payload.get("toolUseId"),
            error_message=error_message,
            raw=payload,
        )

@dataclass(slots=True)
class AssistantRun:
    session_id: str | None
    session_title: str | None
    newest_message_at: datetime | None
    variant: str
    paper: ResolvedPaper | None
    message: str
    model: str
    thinking: bool
    web_search: str
    output_text: str
    reasoning_text: str
    error_message: str | None
    events: list[AssistantStreamEvent]
    raw: list[dict[str, Any]] = field(repr=False)

    @property
    def successful(self) -> bool:
        return self.error_message is None


@dataclass(slots=True)
class AssistantContext:
    session_id: str
    variant: str
    paper: ResolvedPaper | None
    newest_message_at: datetime | None
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "variant": self.variant,
            "paper": self.paper.to_dict() if self.paper else None,
            "newest_message_at": self.newest_message_at.isoformat() if self.newest_message_at else None,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AssistantContext":
        paper_payload = payload.get("paper")
        paper = ResolvedPaper.from_dict(paper_payload) if isinstance(paper_payload, dict) else None
        return cls(
            session_id=str(payload.get("session_id", "")),
            variant=str(payload.get("variant", "homepage") or "homepage"),
            paper=paper,
            newest_message_at=parse_datetime(payload.get("newest_message_at")),
            title=payload.get("title"),
        )


@dataclass(slots=True)
class Author:
    id: str
    full_name: str
    user_id: str | None
    username: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Author":
        return cls(
            id=payload.get("id", ""),
            full_name=payload.get("full_name", ""),
            user_id=payload.get("user_id"),
            username=payload.get("username"),
            raw=payload,
        )


@dataclass(slots=True)
class PaperMetrics:
    questions_count: int
    upvotes_count: int
    downvotes_count: int
    total_votes: int
    public_total_votes: int
    visits: dict[str, int]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "PaperMetrics | None":
        if not payload:
            return None
        return cls(
            questions_count=payload.get("questions_count", 0),
            upvotes_count=payload.get("upvotes_count", 0),
            downvotes_count=payload.get("downvotes_count", 0),
            total_votes=payload.get("total_votes", 0),
            public_total_votes=payload.get("public_total_votes", 0),
            visits=payload.get("visits_count", {}) or {},
            raw=payload,
        )


@dataclass(slots=True)
class ImplementationResource:
    provider: str
    url: str
    description: str | None
    language: str | None
    stars: int | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, provider: str, payload: dict[str, Any]) -> "ImplementationResource":
        return cls(
            provider=provider,
            url=payload.get("url", ""),
            description=payload.get("description"),
            language=payload.get("language"),
            stars=payload.get("stars"),
            raw=payload,
        )


@dataclass(slots=True)
class PaperVersion:
    id: str
    version_label: str
    version_order: int
    title: str
    abstract: str
    publication_date: datetime | None
    license_url: str | None
    created_at: datetime | None
    updated_at: datetime | None
    is_hidden: bool
    image_url: str | None
    universal_paper_id: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PaperVersion":
        return cls(
            id=payload.get("id", ""),
            version_label=payload.get("version_label", ""),
            version_order=payload.get("version_order", 0),
            title=payload.get("title", ""),
            abstract=payload.get("abstract", ""),
            publication_date=parse_datetime(payload.get("publication_date")),
            license_url=payload.get("license"),
            created_at=parse_datetime(payload.get("created_at")),
            updated_at=parse_datetime(payload.get("updated_at")),
            is_hidden=payload.get("is_hidden", False),
            image_url=payload.get("imageURL"),
            universal_paper_id=payload.get("universal_paper_id"),
            raw=payload,
        )


@dataclass(slots=True)
class PaperGroup:
    id: str
    universal_paper_id: str
    title: str
    created_at: datetime | None
    updated_at: datetime | None
    topics: list[str]
    metrics: PaperMetrics | None
    podcast_path: str | None
    source_name: str | None
    source_url: str | None
    is_hidden: bool
    first_publication_date: datetime | None
    variant: str | None
    citation: str | None
    resources: list[ImplementationResource]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PaperGroup":
        resources = []
        for provider, resource_payload in (payload.get("resources") or {}).items():
            if isinstance(resource_payload, dict) and resource_payload.get("url"):
                resources.append(ImplementationResource.from_payload(provider, resource_payload))

        source = payload.get("source") or {}
        citation_payload = payload.get("citation")
        citation = None
        if isinstance(citation_payload, dict):
            citation = citation_payload.get("bibtex")
        elif isinstance(citation_payload, str):
            citation = citation_payload
        return cls(
            id=payload.get("id", ""),
            universal_paper_id=payload.get("universal_paper_id", ""),
            title=payload.get("title", ""),
            created_at=parse_datetime(payload.get("created_at")),
            updated_at=parse_datetime(payload.get("updated_at")),
            topics=list(payload.get("topics") or []),
            metrics=PaperMetrics.from_payload(payload.get("metrics")),
            podcast_path=payload.get("podcast_path"),
            source_name=source.get("name"),
            source_url=source.get("url"),
            is_hidden=payload.get("is_hidden", False),
            first_publication_date=parse_datetime(payload.get("first_publication_date")),
            variant=payload.get("variant"),
            citation=citation,
            resources=resources,
            raw=payload,
        )


@dataclass(slots=True)
class Paper:
    resolved: ResolvedPaper
    version: PaperVersion
    group: PaperGroup
    authors: list[Author]
    verified_authors: list[Author]
    pdf_url: str | None
    implementation: dict[str, Any] | None
    marimo_implementation: dict[str, Any] | None
    organization_info: list[dict[str, Any]]
    comments: list[dict[str, Any]]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, resolved: ResolvedPaper, payload: dict[str, Any]) -> "Paper":
        paper = payload.get("paper") or {}
        version = PaperVersion.from_payload(paper.get("paper_version") or {})
        group = PaperGroup.from_payload(paper.get("paper_group") or {})
        authors = [Author.from_payload(item) for item in paper.get("authors") or []]
        verified_authors = [Author.from_payload(item) for item in paper.get("verified_authors") or []]
        pdf_info = paper.get("pdf_info") or {}
        return cls(
            resolved=resolved,
            version=version,
            group=group,
            authors=authors,
            verified_authors=verified_authors,
            pdf_url=pdf_info.get("fetcher_url"),
            implementation=paper.get("implementation"),
            marimo_implementation=paper.get("marimo_implementation"),
            organization_info=list(paper.get("organization_info") or []),
            comments=list(payload.get("comments") or []),
            raw=payload,
        )


@dataclass(slots=True)
class OverviewSummary:
    summary: str
    original_problem: list[str]
    solution: list[str]
    key_insights: list[str]
    results: list[str]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "OverviewSummary | None":
        if not payload:
            return None
        return cls(
            summary=payload.get("summary", ""),
            original_problem=list(payload.get("originalProblem") or []),
            solution=list(payload.get("solution") or []),
            key_insights=list(payload.get("keyInsights") or []),
            results=list(payload.get("results") or []),
            raw=payload,
        )


@dataclass(slots=True)
class Citation:
    title: str
    full_citation: str
    justification: str | None
    alphaxiv_link: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Citation":
        return cls(
            title=payload.get("title", ""),
            full_citation=payload.get("fullCitation", ""),
            justification=payload.get("justification"),
            alphaxiv_link=payload.get("alphaxivLink"),
            raw=payload,
        )


@dataclass(slots=True)
class PaperOverview:
    version_id: str
    language: str
    title: str
    abstract: str
    summary: OverviewSummary | None
    overview_markdown: str
    intermediate_report: str | None
    citations: list[Citation]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(
        cls, *, version_id: str, language: str, payload: dict[str, Any]
    ) -> "PaperOverview":
        return cls(
            version_id=version_id,
            language=language,
            title=payload.get("title", ""),
            abstract=payload.get("abstract", ""),
            summary=OverviewSummary.from_payload(payload.get("summary")),
            overview_markdown=payload.get("overview", ""),
            intermediate_report=payload.get("intermediateReport"),
            citations=[Citation.from_payload(item) for item in payload.get("citations") or []],
            raw=payload,
        )


@dataclass(slots=True)
class OverviewTranslationStatus:
    language: str
    state: str
    requested_at: datetime | None
    updated_at: datetime | None
    error: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, language: str, payload: dict[str, Any]) -> "OverviewTranslationStatus":
        return cls(
            language=language,
            state=payload.get("state", ""),
            requested_at=parse_timestamp_ms(payload.get("requestedAt")),
            updated_at=parse_timestamp_ms(payload.get("updatedAt")),
            error=payload.get("error"),
            raw=payload,
        )


@dataclass(slots=True)
class OverviewStatus:
    version_id: str
    state: str
    updated_at: datetime | None
    translations: dict[str, OverviewTranslationStatus]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, *, version_id: str, payload: dict[str, Any]) -> "OverviewStatus":
        translations = {
            language: OverviewTranslationStatus.from_payload(language, translation_payload)
            for language, translation_payload in (payload.get("translations") or {}).items()
            if isinstance(translation_payload, dict)
        }
        return cls(
            version_id=version_id,
            state=payload.get("state", ""),
            updated_at=parse_timestamp_ms(payload.get("updatedAt")),
            translations=translations,
            raw=payload,
        )


@dataclass(slots=True)
class PaperTextPage:
    page_number: int
    text: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(
        cls, payload: dict[str, Any], *, fallback_page_number: int
    ) -> "PaperTextPage":
        page_number = payload.get("pageNumber")
        if not isinstance(page_number, int) or page_number <= 0:
            page_number = fallback_page_number
        return cls(
            page_number=page_number,
            text=payload.get("text", ""),
            raw=payload,
        )


@dataclass(slots=True)
class PaperFullText:
    resolved: ResolvedPaper
    pages: list[PaperTextPage]
    raw: dict[str, Any] = field(repr=False)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text)

    @classmethod
    def from_payload(cls, resolved: ResolvedPaper, payload: dict[str, Any]) -> "PaperFullText":
        pages = [
            PaperTextPage.from_payload(page_payload, fallback_page_number=index)
            for index, page_payload in enumerate(payload.get("pages") or [], start=1)
            if isinstance(page_payload, dict)
        ]
        return cls(resolved=resolved, pages=pages, raw=payload)


@dataclass(slots=True)
class PodcastTranscriptLine:
    speaker: str | None
    line: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PodcastTranscriptLine":
        return cls(
            speaker=payload.get("speaker"),
            line=payload.get("line", ""),
            raw=payload,
        )


@dataclass(slots=True)
class PaperTranscript:
    resolved: ResolvedPaper
    transcript_url: str
    lines: list[PodcastTranscriptLine]
    raw: list[dict[str, Any]] = field(repr=False)

    @property
    def text(self) -> str:
        return "\n".join(
            f"{line.speaker}: {line.line}" if line.speaker else line.line for line in self.lines if line.line
        )

    @classmethod
    def from_payload(
        cls,
        *,
        resolved: ResolvedPaper,
        transcript_url: str,
        payload: list[dict[str, Any]],
    ) -> "PaperTranscript":
        lines = [PodcastTranscriptLine.from_payload(item) for item in payload if isinstance(item, dict)]
        return cls(
            resolved=resolved,
            transcript_url=transcript_url,
            lines=lines,
            raw=payload,
        )


@dataclass(slots=True)
class Mention:
    id: str
    post_id: str
    conversation_id: str
    text: str
    posted_at: datetime | None
    author_username: str | None
    author_name: str | None
    author_avatar_url: str | None
    likes: int
    retweets: int
    replies: int
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Mention":
        return cls(
            id=payload.get("id", ""),
            post_id=payload.get("postId", ""),
            conversation_id=payload.get("conversationId", ""),
            text=payload.get("text", ""),
            posted_at=parse_datetime(payload.get("postedAt")),
            author_username=payload.get("authorUsername"),
            author_name=payload.get("authorName"),
            author_avatar_url=payload.get("authorAvatarUrl"),
            likes=payload.get("likes", 0),
            retweets=payload.get("retweets", 0),
            replies=payload.get("replies", 0),
            raw=payload,
        )


@dataclass(slots=True)
class PaperResources:
    resolved: ResolvedPaper
    pdf_url: str | None
    source_url: str | None
    citation: str | None
    podcast_path: str | None
    podcast_url: str | None
    transcript_url: str | None
    implementations: list[ImplementationResource]
    mentions: list[Mention]
    raw: dict[str, Any] = field(repr=False)
