"""Events API implementation."""

from __future__ import annotations

from ._core import BASE_API_URL, ClientCore
from .types import Event


class EventsAPI:
    """Public alphaXiv events operations."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core

    async def list(self) -> list[Event]:
        payload = await self._core.get_json(f"{BASE_API_URL}/events/v1")
        if not isinstance(payload, list):
            return []
        return [Event.from_payload(item) for item in payload if isinstance(item, dict)]
