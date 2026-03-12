"""Authenticated folders support for alphaXiv."""

from __future__ import annotations

from ._core import BASE_API_URL, ClientCore
from .exceptions import AlphaXivError, AuthRequiredError
from .types import Folder

FOLDERS_AUTH_REQUIRED_MESSAGE = (
    "alphaXiv folder endpoints require an API key. Set ALPHAXIV_API_KEY, run "
    "'alphaxiv auth set-api-key', or pass api_key into AlphaXivClient(...)."
)


class FoldersAPI:
    """Authenticated folder operations for alphaXiv."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core

    async def list(self) -> list[Folder]:
        self._require_auth()
        payload = await self._core.get_json(f"{BASE_API_URL}/folders/v3")
        if not isinstance(payload, list):
            raise AlphaXivError("Unexpected folders payload.")
        return [Folder.from_payload(item) for item in payload if isinstance(item, dict)]

    def _require_auth(self) -> None:
        if not self._core.authorization:
            raise AuthRequiredError(FOLDERS_AUTH_REQUIRED_MESSAGE)
