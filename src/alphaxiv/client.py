"""Main async client entrypoint for alphaXiv."""

from __future__ import annotations

from ._comments import CommentsAPI
from ._core import DEFAULT_TIMEOUT, ClientCore
from ._explore import ExploreAPI
from ._folders import FoldersAPI
from ._papers import PapersAPI
from ._search import SearchAPI
from .assistant import AssistantAPI


class AlphaXivClient:
    """Async client for alphaXiv public APIs."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        authorization: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if api_key and authorization:
            raise ValueError("Pass either api_key or authorization, not both.")
        resolved_authorization = authorization or (f"Bearer {api_key}" if api_key else None)
        self._core = ClientCore(authorization=resolved_authorization, timeout=timeout)
        self.search = SearchAPI(self._core)
        self.explore = ExploreAPI(self._core)
        self.papers = PapersAPI(self._core)
        self.folders = FoldersAPI(self._core)
        self.comments = CommentsAPI(self._core)
        self.assistant = AssistantAPI(self._core)

    @classmethod
    def from_saved_api_key(cls, timeout: float = DEFAULT_TIMEOUT) -> AlphaXivClient:
        """Create a client from ALPHAXIV_API_KEY or a locally saved API key."""
        from .auth import load_api_key_value

        api_key = load_api_key_value()
        if not api_key:
            raise ValueError(
                "No alphaXiv API key is configured. Set ALPHAXIV_API_KEY or run "
                "'alphaxiv auth set-api-key'."
            )
        return cls(api_key=api_key, timeout=timeout)

    @classmethod
    def from_api_key(cls, api_key: str, timeout: float = DEFAULT_TIMEOUT) -> AlphaXivClient:
        """Create a client from an explicit alphaXiv API key."""
        return cls(api_key=api_key, timeout=timeout)

    @classmethod
    def from_authorization(
        cls,
        authorization: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> AlphaXivClient:
        """Create a client from an explicit bearer Authorization header value."""
        return cls(authorization=authorization, timeout=timeout)

    @classmethod
    def from_saved_browser_auth(cls, timeout: float = DEFAULT_TIMEOUT) -> AlphaXivClient:
        """Create a client from saved browser-backed alphaXiv auth."""
        from .auth import ensure_saved_browser_auth

        saved_auth = ensure_saved_browser_auth(timeout=timeout)
        if not saved_auth or saved_auth.is_expired:
            raise ValueError(
                "No browser-backed alphaXiv auth is configured. Run 'alphaxiv auth login-web'."
            )
        return cls(authorization=saved_auth.authorization_header, timeout=timeout)

    @classmethod
    def from_saved_auth(
        cls,
        timeout: float = DEFAULT_TIMEOUT,
        *,
        prefer_browser: bool = False,
    ) -> AlphaXivClient:
        """Create a client from saved browser auth or API-key auth."""
        if prefer_browser:
            try:
                return cls.from_saved_browser_auth(timeout=timeout)
            except ValueError:
                return cls.from_saved_api_key(timeout=timeout)

        try:
            return cls.from_saved_api_key(timeout=timeout)
        except ValueError:
            return cls.from_saved_browser_auth(timeout=timeout)

    async def __aenter__(self) -> AlphaXivClient:
        await self._core.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._core.close()

    @property
    def is_connected(self) -> bool:
        return self._core.is_open
