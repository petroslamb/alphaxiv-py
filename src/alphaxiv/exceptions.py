"""Exceptions for alphaxiv-py."""

from __future__ import annotations


class AlphaXivError(Exception):
    """Base exception for alphaxiv-py."""


class APIError(AlphaXivError):
    """Raised when an HTTP or decoding error occurs."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
        response_text: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.response_text = response_text


class ResolutionError(AlphaXivError):
    """Raised when a paper identifier cannot be resolved."""


class AuthRequiredError(AlphaXivError):
    """Raised when the assistant boundary is used without v2 auth support."""
