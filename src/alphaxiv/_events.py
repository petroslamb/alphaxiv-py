"""Events API implementation."""

from __future__ import annotations

from ._core import BASE_API_URL, ClientCore
from .exceptions import APIError
from .types import Event


class EventsAPI:
    """Public alphaXiv events operations."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core

    async def list(self) -> list[Event]:
        payload = await self._core.get_json(f"{BASE_API_URL}/events/v1")
        if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
            raise APIError(
                "Unexpected events response: expected a list of event objects",
                url=f"{BASE_API_URL}/events/v1",
            )
        return [Event.from_payload(item) for item in payload]
