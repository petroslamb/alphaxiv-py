"""Authenticated comment mutations for alphaXiv."""

from __future__ import annotations

import json
from typing import Any

from ._core import BASE_API_URL, ClientCore
from .exceptions import AuthRequiredError

COMMENTS_AUTH_REQUIRED_MESSAGE = (
    "alphaXiv comment mutation endpoints require an API key. Set ALPHAXIV_API_KEY, run "
    "'alphaxiv auth set-api-key', or pass api_key into AlphaXivClient(...)."
)
VALID_COMMENT_TAGS = ("anonymous", "general", "personal", "research", "resources")


def validate_comment_tag(tag: str) -> str:
    normalized = tag.strip().lower()
    if normalized not in VALID_COMMENT_TAGS:
        supported = ", ".join(VALID_COMMENT_TAGS)
        raise ValueError(f"Unsupported comment tag '{tag}'. Expected one of: {supported}.")
    return normalized


class CommentsAPI:
    """Authenticated comment mutation operations for alphaXiv."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core

    async def toggle_upvote(self, comment_id: str) -> dict[str, Any] | None:
        self._require_auth()
        response = await self._core.request(
            "POST",
            f"{BASE_API_URL}/comments/v2/{comment_id}/upvote",
        )
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

    async def delete(self, comment_id: str) -> None:
        self._require_auth()
        await self._core.request(
            "DELETE",
            f"{BASE_API_URL}/comments/v2/{comment_id}",
        )

    def _require_auth(self) -> None:
        if not self._core.authorization:
            raise AuthRequiredError(COMMENTS_AUTH_REQUIRED_MESSAGE)
