"""Paper and resource APIs for alphaXiv."""

from __future__ import annotations

import asyncio
import json
import re
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
from .exceptions import APIError, AuthRequiredError, ResolutionError
from .types import (
    FeedCard,
    Mention,
    OverviewStatus,
    Paper,
    PaperAiDetection,
    PaperComment,
    PaperFigures,
    PaperFullText,
    PaperModelLinks,
    PaperOverview,
    PaperPreview,
    PaperResources,
    PaperTranscript,
    ResolvedPaper,
)

PODCASTS_BASE_URL = "https://paper-podcasts.alphaxiv.org"
_ARXIV_VERSION_RE = re.compile(r"^(?P<bare>\d{4}\.\d{4,5})(?:v(?P<version>\d+))?$")


def _normalize_overview_language(language: str) -> str:
    return language.strip().lower() or "en"


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
            payload = await self._get_legacy_or_direct_payload(identifier, normalized)
            resolved = self._resolved_from_legacy(identifier, payload)
            self._cache_resolution(normalized, resolved)
            return resolved

        if is_bare_arxiv_id(normalized):
            payload = await self._get_legacy_or_direct_payload(identifier, normalized)
            resolved = self._resolved_from_legacy(identifier, payload)
            self._cache_resolution(normalized, resolved)
            return resolved

        resolved = await self._resolve_direct(identifier, normalized)
        self._cache_resolution(normalized, resolved)
        return resolved

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
        language = _normalize_overview_language(language)
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

    async def request_overview_ai(
        self,
        identifier: str,
        *,
        preferred_language: str = "en",
    ) -> dict[str, Any]:
        """Request alphaXiv to generate an AI overview for the paper version.

        This mirrors the web UI's "Generate Overview" button.
        """
        if not self._core.has_auth:
            raise AuthRequiredError("Overview generation requires authentication.")

        preferred_language = _normalize_overview_language(preferred_language)
        normalized = normalize_identifier(identifier)
        match = _ARXIV_VERSION_RE.fullmatch(normalized)
        if not match:
            if is_paper_version_uuid(normalized):
                resolved = await self._resolve_direct(identifier, normalized)
                self._cache_resolution(normalized, resolved)
            else:
                resolved = await self.resolve(identifier)
            normalized = resolved.canonical_id or resolved.versionless_id or normalized
            match = _ARXIV_VERSION_RE.fullmatch(normalized)

        if not match:
            raise ResolutionError(
                "Overview generation requires a bare or versioned arXiv id like 2605.02011 or "
                "2605.02011v1."
            )

        bare = match.group("bare")
        version_str = match.group("version")
        if version_str is None:
            legacy = await self._get_legacy_or_direct_payload(identifier, bare)
            paper = legacy.get("paper")
            version_num = self._version_number_from_legacy_paper(paper)
            if version_num is None:
                raise ResolutionError(
                    f"Could not determine the latest arXiv version for '{identifier}'. "
                    "Try passing an explicit version like 2604.02368v4."
                )
        else:
            try:
                version_num = int(version_str)
            except ValueError as exc:
                raise ResolutionError(f"Invalid arXiv version suffix in '{identifier}'.") from exc

        response = await self._core.request(
            "POST",
            f"{BASE_API_URL}/v2/papers/{bare}/versions/{version_num}/request-ai",
            params={"preferredLanguage": preferred_language},
            json_data={},
        )
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = {"raw": response.text}
        return payload if isinstance(payload, dict) else {"payload": payload}

    async def wait_for_overview(
        self,
        identifier: str,
        *,
        language: str = "en",
        timeout: float = 300.0,
        poll_interval: float = 2.0,
        allow_missing_status: bool = False,
        allow_missing_translation: bool = False,
    ) -> OverviewStatus:
        """Poll overview status until it reaches a terminal state.

        If ``language`` is not the default, waits for the corresponding translation status to
        reach a terminal state as well.
        """
        language = _normalize_overview_language(language)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        last_status: OverviewStatus | None = None
        last_state: str | None = None
        last_url: str | None = None
        last_not_found_error: APIError | None = None
        last_missing_translation_error: APIError | None = None
        pending_states = {"pending", "queued", "running", "processing", "extracting", "generating"}
        success_states = {"done", "complete", "completed", "ready", "success", "succeeded"}
        while True:
            try:
                last_status = await self.overview_status(identifier)
            except APIError as exc:
                # Newly requested overviews can briefly return 404 until the backing record exists.
                if exc.status_code != 404:
                    raise
                last_not_found_error = exc
                if not allow_missing_status:
                    raise
                last_status = None
                last_state = "pending"
                last_url = exc.url or last_url
            else:
                last_not_found_error = None
                last_url = f"{BASE_API_URL}/papers/v3/{last_status.version_id}/overview/status"
                last_state = (last_status.state or "").strip().lower() or None
                if last_state and last_state not in pending_states:
                    if last_state not in success_states:
                        error = last_status.raw.get("error")
                        message = f"Overview generation failed with state '{last_state}'."
                        if error:
                            message = f"{message} Error: {error}"
                        raise APIError(message, status_code=502, url=last_url)
                    if language == "en":
                        last_missing_translation_error = None
                        return last_status
                    translation = last_status.translations.get(language)
                    if translation is None:
                        last_missing_translation_error = APIError(
                            f"Overview translation for '{language}' was not queued after base "
                            f"overview reached {last_state}.",
                            status_code=404,
                            url=last_url,
                        )
                        if not allow_missing_translation:
                            raise last_missing_translation_error
                        last_state = f"{language} translation missing"
                    else:
                        last_missing_translation_error = None
                        translation_state = (translation.state or "").strip().lower() or None
                        if translation_state and translation_state not in pending_states:
                            if translation_state not in success_states:
                                message = (
                                    f"Overview translation failed with state '{translation_state}'."
                                )
                                if translation.error:
                                    message = f"{message} Error: {translation.error}"
                                raise APIError(message, status_code=502, url=last_url)
                            if translation.error:
                                raise APIError(
                                    f"Overview translation failed: {translation.error}",
                                    status_code=502,
                                    url=last_url,
                                )
                            return last_status
            if loop.time() >= deadline:
                if last_not_found_error is not None:
                    raise last_not_found_error
                if last_missing_translation_error is not None:
                    raise last_missing_translation_error
                message = "Overview generation did not complete before timeout."
                if last_state:
                    message = f"{message} Last state: {last_state}."
                raise APIError(message, status_code=408, url=last_url)
            await asyncio.sleep(poll_interval)

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

    async def preview(self, identifier: str) -> PaperPreview:
        normalized = normalize_identifier(identifier)
        if not normalized:
            raise ResolutionError("Paper preview requires a paper identifier.")
        payload = await self._core.get_json(f"{BASE_API_URL}/papers/v3/{normalized}/preview")
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected preview payload for '{identifier}'.")
        return PaperPreview.from_payload(payload)

    async def figures(self, identifier: str) -> PaperFigures:
        group_id = await self._resolve_group_id_for_public_read(identifier)
        payload = await self._core.get_json(f"{BASE_API_URL}/papers/v3/{group_id}/figures")
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected figures payload for '{identifier}'.")
        return PaperFigures.from_payload(paper_group_id=group_id, payload=payload)

    async def ai_detection(self, identifier: str) -> PaperAiDetection | None:
        version_id = await self._resolve_version_id_for_public_read(identifier)
        try:
            payload = await self._core.get_json(
                f"{BASE_API_URL}/papers/v3/{version_id}/ai-detection"
            )
        except APIError as exc:
            if exc.status_code == 404:
                return None
            raise
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected AI-detection payload for '{identifier}'.")
        return PaperAiDetection.from_payload(payload)

    async def model_links(self, identifier: str) -> PaperModelLinks | None:
        version_id = await self._resolve_version_id_for_public_read(identifier)
        try:
            payload = await self._core.get_json(
                f"{BASE_API_URL}/papers/v3/{version_id}/model-links"
            )
        except APIError as exc:
            if exc.status_code == 404:
                return None
            raise
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected model-links payload for '{identifier}'.")
        return PaperModelLinks.from_payload(payload)

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
        user_payload = await self._core.get_json(f"{BASE_API_URL}/users/v3")
        user = user_payload.get("user") if isinstance(user_payload, dict) else None
        if not isinstance(user, dict):
            user = user_payload if isinstance(user_payload, dict) else {}
        voted_groups = user.get("votedPaperGroups") if isinstance(user, dict) else None
        liked = group_id in (voted_groups if isinstance(voted_groups, list) else [])
        response = await self._core.request(
            "POST",
            f"{BASE_API_URL}/papers/v3/{group_id}/like",
            params={"liked": str(not liked).lower()},
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

    async def _get_legacy_or_direct_payload(
        self,
        input_id: str,
        normalized: str,
    ) -> dict[str, Any]:
        try:
            return await self._get_legacy_payload(normalized)
        except APIError as legacy_error:
            try:
                resolved = await self._resolve_direct(input_id, normalized)
            except APIError:
                raise legacy_error from None
            return self._legacy_like_payload_from_resolved(resolved)

    async def _resolve_direct(self, input_id: str, normalized: str) -> ResolvedPaper:
        try:
            payload = await self._core.get_json(f"{BASE_API_URL}/papers/v3/{normalized}")
        except APIError as exc:
            raise ResolutionError(
                f"Could not resolve paper identifier '{input_id}' through alphaXiv."
            ) from exc
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected direct paper payload for '{input_id}'.")
        resolved = self._resolved_from_direct(input_id, payload)
        if not resolved.version_id and not resolved.group_id:
            raise ResolutionError(f"Could not determine paper ids for '{input_id}'.")
        return resolved

    def _resolved_from_direct(self, input_id: str, payload: dict[str, Any]) -> ResolvedPaper:
        versionless_id = (
            payload.get("universalId")
            or payload.get("universal_paper_id")
            or payload.get("universalPaperId")
        )
        version_order = payload.get("versionOrder") or payload.get("version_order")
        canonical_id = payload.get("canonicalId") or payload.get("canonical_id")
        if not canonical_id and versionless_id and isinstance(version_order, int):
            canonical_id = f"{versionless_id}v{version_order}"
        return ResolvedPaper(
            input_id=input_id,
            versionless_id=versionless_id,
            canonical_id=canonical_id,
            version_id=payload.get("versionId") or payload.get("version_id") or payload.get("id"),
            group_id=payload.get("groupId")
            or payload.get("group_id")
            or payload.get("paper_group_id"),
            title=payload.get("title"),
            raw=payload,
        )

    def _legacy_like_payload_from_resolved(self, resolved: ResolvedPaper) -> dict[str, Any]:
        payload = {
            "paper": {
                "paper_version": {
                    "id": resolved.version_id,
                    "version_label": self._version_label_from_canonical(resolved.canonical_id),
                    "title": resolved.title,
                    "universal_paper_id": resolved.versionless_id,
                },
                "paper_group": {
                    "id": resolved.group_id,
                    "title": resolved.title,
                    "universal_paper_id": resolved.versionless_id,
                },
            },
            "comments": [],
        }
        return payload

    def _version_label_from_canonical(self, canonical_id: str | None) -> str | None:
        if not canonical_id or "v" not in canonical_id:
            return None
        return f"v{canonical_id.rsplit('v', 1)[1]}"

    def _version_number_from_legacy_paper(self, paper: Any) -> int | None:
        if not isinstance(paper, dict):
            return None

        max_version_order = self._positive_int(paper.get("max_version_order"))
        if max_version_order is not None:
            return max_version_order

        version = paper.get("paper_version") or {}
        if not isinstance(version, dict):
            return None

        version_order = self._positive_int(version.get("version_order"))
        if version_order is not None:
            return version_order

        version_label = version.get("version_label")
        if not isinstance(version_label, str):
            return None
        match = re.fullmatch(r"v(?P<version>\d+)", version_label.strip())
        if not match:
            return None
        return int(match.group("version"))

    def _positive_int(self, value: Any) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return None
        return value

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

    async def _resolve_group_id_for_public_read(self, identifier: str) -> str:
        normalized = normalize_identifier(identifier)
        if is_paper_version_uuid(normalized):
            if normalized in self._resolution_cache and self._resolution_cache[normalized].group_id:
                return str(self._resolution_cache[normalized].group_id)
            try:
                payload = await self._core.get_json(f"{BASE_API_URL}/papers/v3/{normalized}")
            except APIError as exc:
                if exc.status_code == 404:
                    return normalized
                raise
            if not isinstance(payload, dict):
                raise ResolutionError(f"Unexpected direct paper payload for '{identifier}'.")
            resolved = self._resolved_from_direct(identifier, payload)
            if not resolved.version_id and not resolved.group_id:
                return normalized
            self._cache_resolution(normalized, resolved)
            return self._require_group_id(identifier, resolved, operation="Figures lookup")
        resolved = await self.resolve(identifier)
        return self._require_group_id(identifier, resolved, operation="Figures lookup")

    async def _resolve_version_id_for_public_read(self, identifier: str) -> str:
        normalized = normalize_identifier(identifier)
        if is_paper_version_uuid(normalized):
            return normalized
        resolved = await self.resolve(identifier)
        return self._require_version_id(identifier, resolved, operation="Paper sidecar lookup")

    def _require_auth(self, message: str) -> None:
        if not self._core.has_auth:
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
                "anchorPosition": None,
                "focusPosition": None,
                "highlightRects": None,
                "selectedText": None,
                "highlightColor": None,
            },
        )
        payload = self._response_payload(response)
        if not isinstance(payload, dict):
            raise ResolutionError(f"Unexpected comment creation payload for '{identifier}'.")
        return PaperComment.from_payload(payload)
