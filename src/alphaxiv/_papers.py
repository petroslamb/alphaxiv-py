"""Paper and resource APIs for alphaXiv."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._comments import validate_comment_tag
from ._core import BASE_API_URL, ClientCore
from ._identifiers import (
    is_bare_arxiv_id,
    is_paper_version_uuid,
    is_versioned_arxiv_id,
    normalize_identifier,
)
from .exceptions import AuthRequiredError, ResolutionError
from .types import (
    FeedCard,
    Mention,
    OverviewStatus,
    Paper,
    PaperComment,
    PaperFullText,
    PaperOverview,
    PaperResources,
    PaperTranscript,
    ResolvedPaper,
)

PODCASTS_BASE_URL = "https://paper-podcasts.alphaxiv.org"


class PapersAPI:
    """Paper-related alphaXiv operations."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core
        self._resolution_cache: dict[str, ResolvedPaper] = {}
        self._legacy_cache: dict[str, dict[str, Any]] = {}

    async def resolve(self, identifier: str) -> ResolvedPaper:
        normalized = normalize_identifier(identifier)
        if normalized in self._resolution_cache:
            return self._resolution_cache[normalized]

        if is_paper_version_uuid(normalized):
            resolved = ResolvedPaper(
                input_id=identifier,
                versionless_id=None,
                canonical_id=None,
                version_id=normalized,
                group_id=None,
            )
            self._cache_resolution(normalized, resolved)
            return resolved

        if is_versioned_arxiv_id(normalized):
            payload = await self._get_legacy_payload(normalized)
            resolved = self._resolved_from_legacy(identifier, payload)
            self._cache_resolution(normalized, resolved)
            return resolved

        if is_bare_arxiv_id(normalized):
            payload = await self._get_legacy_payload(normalized)
            resolved = self._resolved_from_legacy(identifier, payload)
            self._cache_resolution(normalized, resolved)
            return resolved

        raise ResolutionError(
            f"Unsupported identifier '{identifier}'. Expected a bare arXiv ID, "
            "versioned arXiv ID, or paper-version UUID."
        )

    async def get(self, identifier: str) -> Paper:
        resolved = await self.resolve(identifier)
        if not resolved.canonical_id:
            raise ResolutionError(
                "Paper metadata lookup requires a bare or versioned arXiv ID. "
                "A paper-version UUID is only sufficient for overview and full-text access."
            )
        payload = await self._get_legacy_payload(resolved.canonical_id)
        resolved = self._resolved_from_legacy(identifier, payload)
        self._cache_resolution(resolved.preferred_id, resolved)
        return Paper.from_payload(resolved, payload)

    async def overview(self, identifier: str, language: str = "en") -> PaperOverview:
        resolved = await self.resolve(identifier)
        if not resolved.version_id:
            raise ResolutionError(f"Could not determine a paper version UUID for '{identifier}'.")
        payload = await self._core.get_json(
            f"{BASE_API_URL}/papers/v3/{resolved.version_id}/overview/{language}"
        )
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected overview payload for '{identifier}'.")
        return PaperOverview.from_payload(
            version_id=resolved.version_id,
            language=language,
            payload=payload,
        )

    async def overview_status(self, identifier: str) -> OverviewStatus:
        resolved = await self.resolve(identifier)
        if not resolved.version_id:
            raise ResolutionError(f"Could not determine a paper version UUID for '{identifier}'.")
        payload = await self._core.get_json(
            f"{BASE_API_URL}/papers/v3/{resolved.version_id}/overview/status"
        )
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected overview status payload for '{identifier}'.")
        return OverviewStatus.from_payload(version_id=resolved.version_id, payload=payload)

    async def full_text(self, identifier: str) -> PaperFullText:
        resolved = await self.resolve(identifier)
        if not resolved.version_id:
            raise ResolutionError(f"Could not determine a paper version UUID for '{identifier}'.")
        payload = await self._core.get_json(
            f"{BASE_API_URL}/papers/v3/{resolved.version_id}/full-text"
        )
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected full-text payload for '{identifier}'.")
        return PaperFullText.from_payload(resolved, payload)

    async def mentions(self, identifier: str) -> list[Mention]:
        resolved = await self.resolve(identifier)
        if not resolved.group_id:
            raise ResolutionError(
                "Mentions lookup requires a resolvable paper group ID. "
                "Use a bare or versioned arXiv ID instead of a paper-version UUID."
            )
        payload = await self._core.get_json(
            f"{BASE_API_URL}/papers/v3/x-mentions-db/{resolved.group_id}"
        )
        if not isinstance(payload, dict):
            return []
        return [Mention.from_payload(item) for item in payload.get("mentions") or []]

    async def comments(self, identifier: str) -> list[PaperComment]:
        resolved = await self.resolve(identifier)
        group_id = self._require_group_id(
            identifier,
            resolved,
            operation="Comments lookup",
        )
        payload = await self._core.get_json(f"{BASE_API_URL}/papers/v3/legacy/{group_id}/comments")
        if not isinstance(payload, list):
            raise ResolutionError(f"Unexpected comments payload for '{identifier}'.")
        return [PaperComment.from_payload(item) for item in payload if isinstance(item, dict)]

    async def create_comment(
        self,
        identifier: str,
        *,
        body: str,
        title: str | None = None,
        tag: str = "general",
    ) -> PaperComment:
        return await self._submit_comment(
            identifier,
            body=body,
            title=title,
            tag=tag,
            parent_comment_id=None,
        )

    async def reply_to_comment(
        self,
        identifier: str,
        parent_comment_id: str,
        *,
        body: str,
        title: str | None = None,
        tag: str = "general",
    ) -> PaperComment:
        return await self._submit_comment(
            identifier,
            body=body,
            title=title,
            tag=tag,
            parent_comment_id=parent_comment_id,
        )

    async def similar(self, identifier: str, limit: int | None = None) -> list[FeedCard]:
        normalized = normalize_identifier(identifier)
        if is_paper_version_uuid(normalized):
            raise ResolutionError(
                "Similar-papers lookup requires a bare or versioned arXiv ID. "
                "UUID inputs are not supported by this endpoint."
            )
        if not is_bare_arxiv_id(normalized) and not is_versioned_arxiv_id(normalized):
            raise ResolutionError(
                f"Unsupported identifier '{identifier}'. Similar-papers lookup requires a bare "
                "or versioned arXiv ID."
            )

        payload = await self._core.get_json(f"{BASE_API_URL}/papers/v3/{normalized}/similar-papers")
        if not isinstance(payload, list):
            raise ResolutionError(f"Unexpected similar-papers payload for '{identifier}'.")

        seen_keys: set[str] = set()
        cards: list[FeedCard] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            card = FeedCard.from_payload(item)
            dedupe_key = card.canonical_id or card.version_id or card.paper_id or card.group_id
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            cards.append(card)

        return cards[:limit] if limit is not None else cards

    async def record_view(self, identifier: str) -> dict[str, Any] | None:
        self._require_auth(
            "alphaXiv paper view endpoints require an API key. Set ALPHAXIV_API_KEY, run "
            "'alphaxiv auth set-api-key', or pass api_key into AlphaXivClient(...)."
        )
        resolved = await self.resolve(identifier)
        group_id = self._require_group_id(
            identifier,
            resolved,
            operation="Paper view recording",
        )
        response = await self._core.request(
            "POST",
            f"{BASE_API_URL}/papers/v3/{group_id}/view",
        )
        return self._response_payload(response)

    async def toggle_vote(self, identifier: str) -> dict[str, Any] | None:
        self._require_auth(
            "alphaXiv paper vote endpoints require an API key. Set ALPHAXIV_API_KEY, run "
            "'alphaxiv auth set-api-key', or pass api_key into AlphaXivClient(...)."
        )
        resolved = await self.resolve(identifier)
        group_id = self._require_group_id(
            identifier,
            resolved,
            operation="Paper vote toggling",
        )
        response = await self._core.request(
            "POST",
            f"{BASE_API_URL}/v2/papers/{group_id}/vote",
        )
        return self._response_payload(response)

    async def resources(self, identifier: str) -> PaperResources:
        paper = await self.get(identifier)
        mentions = await self.mentions(identifier)
        podcast_url, transcript_url = self._podcast_urls(paper.group.podcast_path)
        return PaperResources(
            resolved=paper.resolved,
            pdf_url=paper.pdf_url,
            source_url=paper.group.source_url,
            citation=paper.group.citation,
            podcast_path=paper.group.podcast_path,
            podcast_url=podcast_url,
            transcript_url=transcript_url,
            implementations=paper.group.resources,
            mentions=mentions,
            raw={"paper": paper.raw, "mentions": [item.raw for item in mentions]},
        )

    async def transcript(self, identifier: str) -> PaperTranscript:
        paper = await self.get(identifier)
        _podcast_url, transcript_url = self._podcast_urls(paper.group.podcast_path)
        if not transcript_url:
            raise ResolutionError(f"No podcast transcript was available for '{identifier}'.")
        payload = await self._core.get_json(transcript_url)
        if not isinstance(payload, list):
            raise ResolutionError(f"Unexpected transcript payload for '{identifier}'.")
        return PaperTranscript.from_payload(
            resolved=paper.resolved,
            transcript_url=transcript_url,
            payload=payload,
        )

    async def bibtex(self, identifier: str) -> str | None:
        paper = await self.get(identifier)
        return paper.group.citation

    async def pdf_url(self, identifier: str) -> str:
        paper = await self.get(identifier)
        if not paper.pdf_url:
            raise ResolutionError(f"No PDF URL was available for '{identifier}'.")
        return paper.pdf_url

    async def download_pdf(self, identifier: str, path: str | Path) -> Path:
        pdf_url = await self.pdf_url(identifier)
        return await self._core.download(pdf_url, path)

    async def _get_legacy_payload(self, canonical_id: str) -> dict[str, Any]:
        if canonical_id in self._legacy_cache:
            return self._legacy_cache[canonical_id]
        payload = await self._core.get_json(f"{BASE_API_URL}/papers/v3/legacy/{canonical_id}")
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected legacy paper payload for '{canonical_id}'.")
        self._cache_legacy_payload(canonical_id, payload)
        return payload

    def _resolved_from_legacy(self, input_id: str, payload: dict[str, Any]) -> ResolvedPaper:
        paper = payload.get("paper") or {}
        version = paper.get("paper_version") or {}
        group = paper.get("paper_group") or {}
        versionless_id = group.get("universal_paper_id") or version.get("universal_paper_id")
        version_label = version.get("version_label")
        canonical_id = None
        if versionless_id and version_label:
            canonical_id = f"{versionless_id}{version_label}"
        return ResolvedPaper(
            input_id=input_id,
            versionless_id=versionless_id,
            canonical_id=canonical_id,
            version_id=version.get("id"),
            group_id=group.get("id"),
            title=version.get("title") or group.get("title"),
            raw=payload,
        )

    def _cache_resolution(self, key: str, resolved: ResolvedPaper) -> None:
        aliases = {key, resolved.input_id, resolved.preferred_id}
        if resolved.versionless_id:
            aliases.add(resolved.versionless_id)
        if resolved.canonical_id:
            aliases.add(resolved.canonical_id)
        if resolved.version_id:
            aliases.add(resolved.version_id)
        if resolved.group_id:
            aliases.add(resolved.group_id)
        for alias in aliases:
            self._resolution_cache[alias] = resolved

    def _cache_legacy_payload(self, key: str, payload: dict[str, Any]) -> None:
        aliases = {key}
        paper = payload.get("paper") or {}
        version = paper.get("paper_version") or {}
        group = paper.get("paper_group") or {}
        versionless_id = group.get("universal_paper_id") or version.get("universal_paper_id")
        version_label = version.get("version_label")
        if versionless_id:
            aliases.add(versionless_id)
        if versionless_id and version_label:
            aliases.add(f"{versionless_id}{version_label}")
        for alias in aliases:
            self._legacy_cache[alias] = payload

    def _require_auth(self, message: str) -> None:
        if not self._core.authorization:
            raise AuthRequiredError(message)

    def _require_group_id(
        self,
        identifier: str,
        resolved: ResolvedPaper,
        *,
        operation: str,
    ) -> str:
        if resolved.group_id:
            return resolved.group_id
        raise ResolutionError(
            f"{operation} requires a bare or versioned arXiv ID. "
            f"Could not determine a paper group ID for '{identifier}'."
        )

    def _require_version_id(
        self,
        identifier: str,
        resolved: ResolvedPaper,
        *,
        operation: str,
    ) -> str:
        if resolved.version_id:
            return resolved.version_id
        raise ResolutionError(
            f"{operation} requires a resolvable paper version ID. "
            f"Could not determine a paper version ID for '{identifier}'."
        )

    def _response_payload(self, response: Any) -> dict[str, Any] | None:
        if not response.content:
            return None
        try:
            payload = response.json()
        except json.JSONDecodeError:
            text = response.text.strip()
            return {"text": text} if text else None
        if isinstance(payload, dict):
            return payload
        return {"data": payload}

    def _podcast_urls(self, podcast_path: str | None) -> tuple[str | None, str | None]:
        if not podcast_path:
            return None, None
        normalized_path = podcast_path.lstrip("/")
        directory = normalized_path.rsplit("/", 1)[0]
        podcast_url = f"{PODCASTS_BASE_URL}/{normalized_path}"
        transcript_url = f"{PODCASTS_BASE_URL}/{directory}/transcript.json"
        return podcast_url, transcript_url

    async def _submit_comment(
        self,
        identifier: str,
        *,
        body: str,
        title: str | None,
        tag: str,
        parent_comment_id: str | None,
    ) -> PaperComment:
        self._require_auth(
            "alphaXiv comment creation endpoints require an API key. Set ALPHAXIV_API_KEY, run "
            "'alphaxiv auth set-api-key', or pass api_key into AlphaXivClient(...)."
        )
        normalized_body = body.strip()
        if not normalized_body:
            raise ValueError("Comment body must not be empty.")
        normalized_tag = validate_comment_tag(tag)
        normalized_title = title.strip() if title else None
        resolved = await self.resolve(identifier)
        version_id = self._require_version_id(
            identifier,
            resolved,
            operation="Comment creation",
        )
        response = await self._core.request(
            "POST",
            f"{BASE_API_URL}/papers/v2/{version_id}/comment",
            json_data={
                "body": normalized_body,
                "title": normalized_title or None,
                "tag": normalized_tag,
                "parentCommentId": parent_comment_id,
            },
        )
        payload = self._response_payload(response)
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected comment creation payload for '{identifier}'.")
        return PaperComment.from_payload(payload)
