"""Shared HTTP client infrastructure for alphaXiv APIs."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx

from .exceptions import APIError

BASE_API_URL = "https://api.alphaxiv.org"
BASE_WEB_URL = "https://www.alphaxiv.org"
DEFAULT_TIMEOUT = 30.0
DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_RETRIES = 2
USER_AGENT = "alphaxiv-py/0.1.0"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class ClientCore:
    """Shared HTTP functionality for AlphaXivClient sub-APIs."""

    def __init__(
        self,
        *,
        authorization: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ) -> None:
        self.authorization = authorization
        self._timeout = timeout
        self._connect_timeout = connect_timeout
        self._retries = retries
        self._http_client: httpx.AsyncClient | None = None

    async def open(self) -> None:
        if self._http_client is not None:
            return
        timeout = httpx.Timeout(
            connect=self._connect_timeout,
            read=self._timeout,
            write=self._timeout,
            pool=self._timeout,
        )
        headers = {"User-Agent": USER_AGENT}
        if self.authorization:
            headers["Authorization"] = self.authorization
        self._http_client = httpx.AsyncClient(timeout=timeout, headers=headers)

    async def close(self) -> None:
        if self._http_client is None:
            return
        await self._http_client.aclose()
        self._http_client = None

    @property
    def is_open(self) -> bool:
        return self._http_client is not None

    def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            raise RuntimeError("Client not initialized. Use 'async with AlphaXivClient()'.")
        return self._http_client

    def _build_api_error(self, *, method: str, response: httpx.Response, text: str) -> APIError:
        message = f"{method} {response.request.url} failed with HTTP {response.status_code}"
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict) and error.get("message"):
                message = str(error["message"])
            elif payload.get("message"):
                message = str(payload["message"])
        return APIError(
            message,
            status_code=response.status_code,
            url=str(response.url),
            response_text=text[:1000],
        )

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool = False,
        json_data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make a request with basic retry handling."""
        client = self._client()
        for attempt in range(self._retries + 1):
            try:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    follow_redirects=follow_redirects,
                    json=json_data,
                )
            except httpx.RequestError as exc:
                if attempt >= self._retries:
                    raise APIError(str(exc), url=url) from exc
                await asyncio.sleep(0.25 * (2**attempt))
                continue

            if response.status_code in RETRY_STATUSES and attempt < self._retries:
                retry_after = response.headers.get("retry-after")
                delay = (
                    float(retry_after)
                    if retry_after and retry_after.isdigit()
                    else 0.25 * (2**attempt)
                )
                await asyncio.sleep(delay)
                continue

            if response.status_code >= 400:
                raise self._build_api_error(method=method, response=response, text=response.text)

            return response

        raise APIError("Request retries exhausted", url=url)

    @asynccontextmanager
    async def stream_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool = False,
        json_data: dict[str, Any] | None = None,
    ):
        """Stream a request body while preserving normal alphaXiv error handling."""
        client = self._client()
        async with client.stream(
            method,
            url,
            params=params,
            headers=headers,
            follow_redirects=follow_redirects,
            json=json_data,
        ) as response:
            if response.status_code >= 400:
                text = (await response.aread()).decode("utf-8", errors="replace")
                raise self._build_api_error(method=method, response=response, text=text)
            yield response

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        follow_redirects: bool = False,
    ) -> dict[str, Any] | list[Any]:
        response = await self.request(
            "GET",
            url,
            params=params,
            follow_redirects=follow_redirects,
        )
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise APIError(
                "Response was not valid JSON",
                status_code=response.status_code,
                url=str(response.url),
                response_text=response.text[:1000],
            ) from exc

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        follow_redirects: bool = False,
    ) -> str:
        response = await self.request(
            "GET",
            url,
            params=params,
            follow_redirects=follow_redirects,
        )
        return response.text

    async def download(self, url: str, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        client = self._client()
        async with client.stream("GET", url, follow_redirects=True) as response:
            if response.status_code >= 400:
                raise APIError(
                    f"Download failed with HTTP {response.status_code}",
                    status_code=response.status_code,
                    url=str(response.url),
                    response_text=(await response.aread()).decode("utf-8", errors="replace")[:1000],
                )
            with output_path.open("wb") as handle:
                async for chunk in response.aiter_bytes():
                    handle.write(chunk)
        return output_path
