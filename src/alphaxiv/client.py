"""Main async client entrypoint for alphaXiv."""

from __future__ import annotations

from ._core import DEFAULT_TIMEOUT, ClientCore
from ._explore import ExploreAPI
from ._papers import PapersAPI
from ._search import SearchAPI
from .assistant import AssistantAPI


class AlphaXivClient:
    """Async client for alphaXiv public APIs."""

    def __init__(self, authorization: str | None = None, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._core = ClientCore(authorization=authorization, timeout=timeout)
        self.search = SearchAPI(self._core)
        self.explore = ExploreAPI(self._core)
        self.papers = PapersAPI(self._core)
        self.assistant = AssistantAPI(self._core)

    @classmethod
    def from_saved_auth(cls, timeout: float = DEFAULT_TIMEOUT) -> "AlphaXivClient":
        """Create a client that reuses auth saved by `alphaxiv login`."""
        from .auth import load_authorization

        return cls(authorization=load_authorization(), timeout=timeout)

    async def __aenter__(self) -> "AlphaXivClient":
        await self._core.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._core.close()

    @property
    def is_connected(self) -> bool:
        return self._core.is_open
