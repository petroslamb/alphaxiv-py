"""Paper and resource APIs for alphaXiv."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._core import BASE_API_URL, BASE_WEB_URL, ClientCore
from ._identifiers import (
    extract_resolution_from_html,
    is_bare_arxiv_id,
    is_paper_version_uuid,
    is_versioned_arxiv_id,
    normalize_identifier,
)
from .exceptions import ResolutionError
from .types import (
    Mention,
    OverviewStatus,
    Paper,
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
            html = await self._core.get_text(f"{BASE_WEB_URL}/abs/{normalized}")
            canonical_id, version_id, group_id = extract_resolution_from_html(html, normalized)
            payload = await self._get_legacy_payload(canonical_id)
            resolved = self._resolved_from_legacy(identifier, payload)
            if not resolved.version_id:
                resolved.version_id = version_id
            if not resolved.group_id:
                resolved.group_id = group_id
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
        self._legacy_cache[canonical_id] = payload
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

    def _podcast_urls(self, podcast_path: str | None) -> tuple[str | None, str | None]:
        if not podcast_path:
            return None, None
        normalized_path = podcast_path.lstrip("/")
        directory = normalized_path.rsplit("/", 1)[0]
        podcast_url = f"{PODCASTS_BASE_URL}/{normalized_path}"
        transcript_url = f"{PODCASTS_BASE_URL}/{directory}/transcript.json"
        return podcast_url, transcript_url
