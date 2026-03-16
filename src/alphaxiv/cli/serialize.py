"""Normalized JSON output helpers for CLI commands."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..types import (
    AssistantContext,
    AssistantMessage,
    AssistantSession,
    Author,
    Citation,
    CommentAuthor,
    ExploreFilterOptions,
    FeedCard,
    FeedFilterSearchResults,
    Folder,
    FolderPaper,
    HomepageSearchResults,
    ImplementationResource,
    Mention,
    OrganizationResult,
    OverviewStatus,
    OverviewSummary,
    OverviewTranslationStatus,
    Paper,
    PaperComment,
    PaperFullText,
    PaperOverview,
    PaperResources,
    PaperTextPage,
    PaperTranscript,
    PodcastTranscriptLine,
    ResolvedPaper,
    SearchResult,
    UrlMetadata,
)
from .messages import usage_error


def isoformat_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def reject_raw_and_json(raw: bool, json_output: bool, *, see_help: str) -> None:
    """Reject commands that try to use raw and json output simultaneously."""
    if raw and json_output:
        raise usage_error(
            "Use either --raw or --json, not both.",
            suggestions=(see_help.replace(" --help", " --json"),),
            see_help=see_help,
        )


def serialize_resolved_paper(resolved: ResolvedPaper | None) -> dict[str, Any] | None:
    if resolved is None:
        return None
    return {
        "preferred_id": resolved.preferred_id,
        "input_id": resolved.input_id,
        "title": resolved.title,
        "versionless_id": resolved.versionless_id,
        "canonical_id": resolved.canonical_id,
        "version_id": resolved.version_id,
        "group_id": resolved.group_id,
    }


def serialize_search_result(result: SearchResult) -> dict[str, Any]:
    return {
        "paper_id": result.paper_id,
        "title": result.title,
        "link": result.link,
        "snippet": result.snippet,
    }


def serialize_organization_result(result: OrganizationResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "name": result.name,
        "slug": result.slug,
        "image": result.image,
    }


def serialize_homepage_search(results: HomepageSearchResults) -> dict[str, Any]:
    return {
        "query": results.query,
        "papers": [serialize_search_result(item) for item in results.papers],
        "topics": list(results.topics),
        "organizations": [serialize_organization_result(item) for item in results.organizations],
    }


def serialize_feed_card(card: FeedCard) -> dict[str, Any]:
    return {
        "paper_id": card.paper_id,
        "canonical_id": card.canonical_id,
        "version_id": card.version_id,
        "group_id": card.group_id,
        "title": card.title,
        "abstract": card.abstract,
        "summary": card.summary,
        "publication_date": isoformat_or_none(card.publication_date),
        "updated_at": isoformat_or_none(card.updated_at),
        "topics": list(card.topics),
        "organizations": list(card.organizations),
        "authors": list(card.authors),
        "result_highlights": list(card.result_highlights),
        "links": {
            "alphaxiv": card.link,
            "github": card.github_url,
        },
        "metrics": {
            "upvotes": card.upvotes,
            "total_votes": card.total_votes,
            "visits": card.visits,
            "visits_last_7_days": card.visits_last_7_days,
            "github_stars": card.github_stars,
            "x_likes": card.x_likes,
        },
    }


def serialize_author(author: Author) -> dict[str, Any]:
    return {
        "id": author.id,
        "full_name": author.full_name,
        "user_id": author.user_id,
        "username": author.username,
    }


def serialize_paper(paper: Paper, *, requested_id: str | None = None) -> dict[str, Any]:
    return {
        "requested_id": requested_id,
        "resolved": serialize_resolved_paper(paper.resolved),
        "title": paper.version.title,
        "abstract": paper.version.abstract,
        "publication_date": isoformat_or_none(paper.version.publication_date),
        "authors": [serialize_author(author) for author in paper.authors],
        "verified_authors": [serialize_author(author) for author in paper.verified_authors],
        "topics": list(paper.group.topics),
        "links": {
            "pdf_url": paper.pdf_url,
            "source_url": paper.group.source_url,
        },
        "metrics": {
            "questions_count": paper.group.metrics.questions_count if paper.group.metrics else None,
            "upvotes_count": paper.group.metrics.upvotes_count if paper.group.metrics else None,
            "downvotes_count": paper.group.metrics.downvotes_count if paper.group.metrics else None,
            "total_votes": paper.group.metrics.total_votes if paper.group.metrics else None,
            "public_total_votes": paper.group.metrics.public_total_votes
            if paper.group.metrics
            else None,
            "visits": paper.group.metrics.visits if paper.group.metrics else None,
        },
        "organizations": list(paper.organization_info),
        "implementation": paper.implementation,
        "marimo_implementation": paper.marimo_implementation,
    }


def serialize_overview_summary(summary: OverviewSummary | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    return {
        "summary": summary.summary,
        "original_problem": list(summary.original_problem),
        "solution": list(summary.solution),
        "key_insights": list(summary.key_insights),
        "results": list(summary.results),
    }


def serialize_citation(citation: Citation) -> dict[str, Any]:
    return {
        "title": citation.title,
        "full_citation": citation.full_citation,
        "justification": citation.justification,
        "alphaxiv_link": citation.alphaxiv_link,
    }


def serialize_paper_overview(
    overview: PaperOverview,
    *,
    requested_id: str | None = None,
) -> dict[str, Any]:
    return {
        "requested_id": requested_id,
        "version_id": overview.version_id,
        "language": overview.language,
        "title": overview.title,
        "abstract": overview.abstract,
        "summary": serialize_overview_summary(overview.summary),
        "overview_markdown": overview.overview_markdown,
        "intermediate_report": overview.intermediate_report,
        "citations": [serialize_citation(item) for item in overview.citations],
    }


def serialize_translation_status(status: OverviewTranslationStatus) -> dict[str, Any]:
    return {
        "language": status.language,
        "state": status.state,
        "requested_at": isoformat_or_none(status.requested_at),
        "updated_at": isoformat_or_none(status.updated_at),
        "error": status.error,
    }


def serialize_overview_status(
    status: OverviewStatus,
    *,
    requested_id: str | None = None,
) -> dict[str, Any]:
    return {
        "requested_id": requested_id,
        "version_id": status.version_id,
        "state": status.state,
        "updated_at": isoformat_or_none(status.updated_at),
        "translations": [
            serialize_translation_status(item)
            for item in sorted(status.translations.values(), key=lambda item: item.language)
        ],
    }


def serialize_implementation(item: ImplementationResource) -> dict[str, Any]:
    return {
        "provider": item.provider,
        "url": item.url,
        "description": item.description,
        "language": item.language,
        "stars": item.stars,
    }


def serialize_mention(item: Mention) -> dict[str, Any]:
    return {
        "id": item.id,
        "post_id": item.post_id,
        "conversation_id": item.conversation_id,
        "text": item.text,
        "posted_at": isoformat_or_none(item.posted_at),
        "author_username": item.author_username,
        "author_name": item.author_name,
        "author_avatar_url": item.author_avatar_url,
        "likes": item.likes,
        "retweets": item.retweets,
        "replies": item.replies,
    }


def serialize_paper_resources(
    resources: PaperResources,
    *,
    requested_id: str | None = None,
) -> dict[str, Any]:
    return {
        "requested_id": requested_id,
        "resolved": serialize_resolved_paper(resources.resolved),
        "links": {
            "pdf_url": resources.pdf_url,
            "source_url": resources.source_url,
            "podcast_path": resources.podcast_path,
            "podcast_url": resources.podcast_url,
            "transcript_url": resources.transcript_url,
        },
        "citation": resources.citation,
        "implementations": [serialize_implementation(item) for item in resources.implementations],
        "mentions": [serialize_mention(item) for item in resources.mentions],
    }


def serialize_podcast_line(line: PodcastTranscriptLine) -> dict[str, Any]:
    return {
        "speaker": line.speaker,
        "line": line.line,
    }


def serialize_transcript(
    transcript: PaperTranscript,
    *,
    requested_id: str | None = None,
) -> dict[str, Any]:
    return {
        "requested_id": requested_id,
        "resolved": serialize_resolved_paper(transcript.resolved),
        "transcript_url": transcript.transcript_url,
        "lines": [serialize_podcast_line(line) for line in transcript.lines],
        "text": transcript.text,
    }


def serialize_text_page(page: PaperTextPage) -> dict[str, Any]:
    return {
        "page_number": page.page_number,
        "text": page.text,
    }


def serialize_full_text(
    full_text: PaperFullText,
    *,
    requested_id: str | None = None,
    requested_pages: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "requested_id": requested_id,
        "resolved": serialize_resolved_paper(full_text.resolved),
        "page_count": full_text.page_count,
        "requested_pages": requested_pages,
        "text": full_text.text,
        "pages": [serialize_text_page(page) for page in full_text.pages],
    }


def serialize_comment_author(author: CommentAuthor | None) -> dict[str, Any] | None:
    if author is None:
        return None
    return {
        "id": author.id,
        "display_name": author.display_name,
        "username": author.username,
        "real_name": author.real_name,
        "avatar_url": author.avatar_url,
        "institution": author.institution,
        "reputation": author.reputation,
        "verified": author.verified,
        "role": author.role,
    }


def serialize_paper_comment(comment: PaperComment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "paper_group_id": comment.paper_group_id,
        "paper_version_id": comment.paper_version_id,
        "parent_comment_id": comment.parent_comment_id,
        "title": comment.title,
        "body": comment.body,
        "tag": comment.tag,
        "upvotes": comment.upvotes,
        "has_upvoted": comment.has_upvoted,
        "has_downvoted": comment.has_downvoted,
        "has_flagged": comment.has_flagged,
        "is_author": comment.is_author,
        "was_edited": comment.was_edited,
        "universal_id": comment.universal_id,
        "paper_title": comment.paper_title,
        "author_responded": comment.author_responded,
        "date": isoformat_or_none(comment.date),
        "author": serialize_comment_author(comment.author),
        "endorsements": list(comment.endorsements),
        "responses": [serialize_paper_comment(item) for item in comment.responses],
    }


def serialize_folder_paper(paper: FolderPaper) -> dict[str, Any]:
    return {
        "paper_group_id": paper.paper_group_id,
        "preferred_id": paper.preferred_id,
        "universal_paper_id": paper.universal_paper_id,
        "canonical_id": paper.canonical_id,
        "version_id": paper.version_id,
        "title": paper.title,
        "abstract": paper.abstract,
        "topics": list(paper.topics),
        "authors": list(paper.authors),
        "added_at": isoformat_or_none(paper.added_at),
    }


def serialize_folder(folder: Folder, *, include_papers: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": folder.id,
        "name": folder.name,
        "type": folder.folder_type,
        "order": folder.order,
        "parent_id": folder.parent_id,
        "sharing_status": folder.sharing_status,
        "paper_count": folder.paper_count,
    }
    if include_papers:
        data["papers"] = [serialize_folder_paper(item) for item in folder.papers]
    return data


def serialize_url_metadata(metadata: UrlMetadata) -> dict[str, Any]:
    return {
        "url": metadata.url,
        "title": metadata.title,
        "description": metadata.description,
        "image_url": metadata.image_url,
        "favicon": metadata.favicon,
        "site_name": metadata.site_name,
        "author": metadata.author,
    }


def serialize_assistant_session(session: AssistantSession) -> dict[str, Any]:
    return {
        "session_id": session.id,
        "title": session.title,
        "newest_message_at": isoformat_or_none(session.newest_message_at),
    }


def serialize_assistant_message(message: AssistantMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "type": message.message_type,
        "parent_message_id": message.parent_message_id,
        "selected_at": isoformat_or_none(message.selected_at),
        "tool_use_id": message.tool_use_id,
        "kind": message.kind,
        "content": message.content,
        "model": message.model,
        "feedback": {
            "type": message.feedback_type,
            "category": message.feedback_category,
            "details": message.feedback_details,
        },
    }


def serialize_assistant_context(context: AssistantContext | None) -> dict[str, Any] | None:
    if context is None:
        return None
    return {
        "session_id": context.session_id,
        "variant": context.variant,
        "title": context.title,
        "newest_message_at": isoformat_or_none(context.newest_message_at),
        "paper": serialize_resolved_paper(context.paper),
    }


def serialize_feed_filter_search(results: FeedFilterSearchResults) -> dict[str, Any]:
    return {
        "query": results.query,
        "topics": list(results.topics),
        "organizations": [serialize_organization_result(item) for item in results.organizations],
    }


def serialize_filter_options(options: ExploreFilterOptions) -> dict[str, Any]:
    return {
        "sorts": list(options.sorts),
        "menu_categories": list(options.menu_categories),
        "intervals": list(options.intervals),
        "sources": list(options.sources),
        "organizations": [serialize_organization_result(item) for item in options.organizations],
    }
