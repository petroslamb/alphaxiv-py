"""API-key and browser-backed auth helpers."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import sys
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from ._core import BASE_API_URL, DEFAULT_TIMEOUT, USER_AGENT
from .exceptions import APIError
from .paths import (
    ensure_home_path,
    get_api_key_path,
    get_browser_auth_path,
    get_browser_profile_path,
)

ALPHAXIV_API_KEY_ENV = "ALPHAXIV_API_KEY"
LOCAL_STORAGE_TOKEN_KEYS = (
    "alphaxiv_client_api_key",
    "alphaxiv_client_api_key_original",
    "alphaxiv_client_api_key_impersonation",
)


def _coalesce_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _nested_get(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _decode_token_expiry(access_token: str) -> datetime | None:
    parts = access_token.split(".")
    if len(parts) != 3:
        return None
    payload_segment = parts[1]
    payload_segment += "=" * (-len(payload_segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload_segment.encode("utf-8"))
        payload = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int):
        return None
    try:
        return datetime.fromtimestamp(exp, tz=UTC)
    except (OverflowError, OSError, ValueError):
        return None


def _normalize_bearer_secret(secret: str) -> str:
    cleaned = secret.strip()
    if cleaned.lower().startswith("bearer "):
        return cleaned[7:].strip()
    return cleaned


def _normalize_api_key(secret: str) -> str:
    return _normalize_bearer_secret(secret)


def _looks_like_api_key(secret: str) -> bool:
    return secret.startswith("axv1_")


def _detect_bearer_auth_kind(access_token: str) -> str:
    if _looks_like_api_key(access_token):
        return "api_key"
    if _decode_token_expiry(access_token) is not None:
        return "session_token"
    return "bearer_token"


def _saved_user_id(user: dict[str, Any]) -> str | None:
    return _coalesce_string(
        user.get("id"),
        user.get("user_id"),
        user.get("userId"),
        _nested_get(user, "user", "id"),
    )


def _saved_display_name(user: dict[str, Any]) -> str | None:
    return _coalesce_string(
        user.get("name"),
        user.get("full_name"),
        user.get("fullName"),
        user.get("username"),
        user.get("handle"),
        _nested_get(user, "user", "name"),
        _nested_get(user, "user", "full_name"),
        _nested_get(user, "user", "username"),
    )


def _saved_email(user: dict[str, Any]) -> str | None:
    email_addresses = user.get("email_addresses")
    primary_email = None
    if isinstance(email_addresses, list):
        for item in email_addresses:
            if isinstance(item, dict):
                primary_email = _coalesce_string(
                    item.get("email_address"),
                    item.get("email"),
                )
                if primary_email:
                    break
    return _coalesce_string(
        user.get("email"),
        user.get("email_address"),
        user.get("primary_email"),
        primary_email,
        _nested_get(user, "user", "email"),
    )


@dataclass(slots=True)
class SavedApiKey:
    """Resolved alphaXiv API key from disk or the environment."""

    api_key: str
    saved_at: datetime
    source: str = "saved"
    user: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def authorization_header(self) -> str:
        return f"Bearer {self.api_key}"

    @property
    def key_prefix(self) -> str:
        parts = self.api_key.split("_")
        if len(parts) >= 3 and parts[1]:
            return f"{parts[0]}_{parts[1]}"
        return self.api_key[:12]

    @property
    def user_id(self) -> str | None:
        return _saved_user_id(self.user)

    @property
    def display_name(self) -> str | None:
        return _saved_display_name(self.user)

    @property
    def email(self) -> str | None:
        return _saved_email(self.user)

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_key": self.api_key,
            "saved_at": self.saved_at.isoformat(),
            "user": self.user,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SavedApiKey:
        user_payload = payload.get("user")
        return cls(
            api_key=_normalize_api_key(str(payload.get("api_key", ""))),
            saved_at=_parse_iso_datetime(payload.get("saved_at")) or datetime.now(UTC),
            source="saved",
            user=cast(dict[str, Any], user_payload) if isinstance(user_payload, dict) else {},
        )


@dataclass(slots=True)
class SavedBrowserAuth:
    """Resolved alphaXiv browser-backed bearer auth from disk or a Playwright profile."""

    access_token: str
    created_at: datetime
    expires_at: datetime | None = None
    kind: str = "bearer_token"
    source: str = "saved"
    user: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def authorization_header(self) -> str:
        return f"Bearer {self.access_token}"

    @property
    def token_prefix(self) -> str:
        return self.access_token[:12]

    @property
    def user_id(self) -> str | None:
        return _saved_user_id(self.user)

    @property
    def display_name(self) -> str | None:
        return _saved_display_name(self.user)

    @property
    def email(self) -> str | None:
        return _saved_email(self.user)

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "kind": self.kind,
            "source": self.source,
            "user": self.user,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SavedBrowserAuth:
        user_payload = payload.get("user")
        access_token = _normalize_bearer_secret(str(payload.get("access_token", "")))
        return cls(
            access_token=access_token,
            created_at=_parse_iso_datetime(payload.get("created_at")) or datetime.now(UTC),
            expires_at=_parse_iso_datetime(payload.get("expires_at")),
            kind=(
                str(payload.get("kind")).strip()
                if isinstance(payload.get("kind"), str) and str(payload.get("kind")).strip()
                else _detect_bearer_auth_kind(access_token)
            ),
            source=(
                str(payload.get("source")).strip()
                if isinstance(payload.get("source"), str) and str(payload.get("source")).strip()
                else "saved"
            ),
            user=cast(dict[str, Any], user_payload) if isinstance(user_payload, dict) else {},
        )


def build_saved_api_key(
    api_key: str,
    *,
    user: dict[str, Any] | None = None,
    source: str = "saved",
    saved_at: datetime | None = None,
) -> SavedApiKey:
    """Construct a SavedApiKey instance from an alphaXiv API key."""
    normalized = _normalize_api_key(api_key)
    return SavedApiKey(
        api_key=normalized,
        saved_at=saved_at or datetime.now(UTC),
        source=source,
        user=user or {},
    )


def build_saved_browser_auth(
    access_token: str,
    *,
    user: dict[str, Any] | None = None,
    kind: str | None = None,
    source: str = "saved",
    created_at: datetime | None = None,
) -> SavedBrowserAuth:
    """Construct a SavedBrowserAuth instance from a bearer token."""
    normalized = _normalize_bearer_secret(access_token)
    return SavedBrowserAuth(
        access_token=normalized,
        created_at=created_at or datetime.now(UTC),
        expires_at=_decode_token_expiry(normalized),
        kind=kind or _detect_bearer_auth_kind(normalized),
        source=source,
        user=user or {},
    )


def load_saved_api_key(path: Path | None = None) -> SavedApiKey | None:
    """Load the locally saved API key, if present."""
    api_key_path = path or get_api_key_path()
    if not api_key_path.exists():
        return None
    try:
        payload = json.loads(api_key_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    saved_api_key = SavedApiKey.from_dict(payload)
    if not saved_api_key.api_key or not _looks_like_api_key(saved_api_key.api_key):
        return None
    return saved_api_key


def load_saved_browser_auth(path: Path | None = None) -> SavedBrowserAuth | None:
    """Load the locally saved browser-backed bearer auth, if present."""
    auth_path = path or get_browser_auth_path()
    if not auth_path.exists():
        return None
    try:
        payload = json.loads(auth_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    saved_auth = SavedBrowserAuth.from_dict(payload)
    if not saved_auth.access_token:
        return None
    return saved_auth


def load_env_api_key() -> SavedApiKey | None:
    """Load an API key from ALPHAXIV_API_KEY when present."""
    api_key = os.environ.get(ALPHAXIV_API_KEY_ENV)
    if not api_key:
        return None
    normalized = _normalize_api_key(api_key)
    if not normalized or not _looks_like_api_key(normalized):
        return None
    return SavedApiKey(
        api_key=normalized,
        saved_at=datetime.now(UTC),
        source="env",
        user={},
    )


def resolve_api_key(timeout: float = DEFAULT_TIMEOUT) -> SavedApiKey | None:
    """Load the effective alphaXiv API key from env or disk."""
    _ = timeout
    env_api_key = load_env_api_key()
    if env_api_key:
        return env_api_key
    return load_saved_api_key()


def ensure_saved_browser_auth(timeout: float = DEFAULT_TIMEOUT) -> SavedBrowserAuth | None:
    """Load saved browser auth and refresh it from the browser profile when needed."""
    saved_auth = load_saved_browser_auth()
    if saved_auth and not saved_auth.is_expired:
        return saved_auth
    refreshed_auth = refresh_saved_browser_auth(timeout=timeout)
    return refreshed_auth or saved_auth


def load_api_key_value() -> str | None:
    """Load the effective alphaXiv API key value, if present."""
    saved_api_key = resolve_api_key()
    if not saved_api_key:
        return None
    return saved_api_key.api_key


def save_api_key(saved_api_key: SavedApiKey, path: Path | None = None) -> Path:
    """Persist an API key to disk with owner-only permissions."""
    ensure_home_path()
    api_key_path = path or get_api_key_path()
    api_key_path.parent.mkdir(parents=True, exist_ok=True)
    api_key_path.write_text(json.dumps(saved_api_key.to_dict(), indent=2))
    api_key_path.chmod(0o600)
    return api_key_path


def save_browser_auth(saved_auth: SavedBrowserAuth, path: Path | None = None) -> Path:
    """Persist browser-backed auth to disk with owner-only permissions."""
    ensure_home_path()
    auth_path = path or get_browser_auth_path()
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(json.dumps(saved_auth.to_dict(), indent=2))
    auth_path.chmod(0o600)
    return auth_path


def clear_saved_api_key(*, path: Path | None = None) -> None:
    """Remove the saved API key."""
    api_key_path = path or get_api_key_path()
    if api_key_path.exists():
        api_key_path.unlink()


def clear_saved_browser_auth(
    *,
    path: Path | None = None,
    clear_browser_profile: bool = False,
) -> None:
    """Remove the saved browser auth and optionally the Playwright profile."""
    auth_path = path or get_browser_auth_path()
    if auth_path.exists():
        auth_path.unlink()
    if clear_browser_profile:
        profile_path = get_browser_profile_path()
        if profile_path.exists():
            shutil.rmtree(profile_path)


def fetch_current_user(access_token: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Validate a bearer token against alphaXiv's authenticated user endpoint."""
    headers = {
        "Authorization": f"Bearer {_normalize_bearer_secret(access_token)}",
        "User-Agent": USER_AGENT,
    }
    try:
        with httpx.Client(timeout=timeout, headers=headers) as client:
            response = client.get(f"{BASE_API_URL}/users/v3")
    except httpx.RequestError as exc:
        raise APIError(str(exc), url=f"{BASE_API_URL}/users/v3") from exc

    if response.status_code >= 400:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = None
        message = f"GET {BASE_API_URL}/users/v3 failed with HTTP {response.status_code}"
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict) and error.get("message"):
                message = str(error["message"])
            elif payload.get("message"):
                message = str(payload["message"])
        raise APIError(
            message,
            status_code=response.status_code,
            url=f"{BASE_API_URL}/users/v3",
            response_text=response.text[:1000],
        )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise APIError(
            "Response was not valid JSON",
            status_code=response.status_code,
            url=f"{BASE_API_URL}/users/v3",
            response_text=response.text[:1000],
        ) from exc

    if isinstance(payload, dict):
        user_payload = payload.get("user")
        if isinstance(user_payload, dict):
            return user_payload
        return payload
    return {"raw": payload}


def authenticate_with_api_key(api_key: str, timeout: float = DEFAULT_TIMEOUT) -> SavedApiKey:
    """Validate and package an explicit alphaXiv API key."""
    normalized = _normalize_api_key(api_key)
    if not normalized:
        raise RuntimeError("API key cannot be empty.")
    if not _looks_like_api_key(normalized):
        raise RuntimeError("alphaXiv API keys must start with 'axv1_'.")
    user_payload = fetch_current_user(normalized, timeout=timeout)
    return build_saved_api_key(normalized, user=user_payload, source="saved")


def refresh_saved_browser_auth(timeout: float = DEFAULT_TIMEOUT) -> SavedBrowserAuth | None:
    """Refresh the saved browser auth from the persistent Playwright profile."""
    browser_profile = get_browser_profile_path()
    if not browser_profile.exists():
        return None
    try:
        access_token = _extract_access_token_for_refresh()
    except RuntimeError:
        return None
    if not access_token:
        return None
    user_payload = fetch_current_user(access_token, timeout=timeout)
    saved_auth = build_saved_browser_auth(
        access_token,
        user=user_payload,
        source="browser_profile",
    )
    save_browser_auth(saved_auth)
    return saved_auth


def authenticate_with_browser() -> SavedBrowserAuth:
    """Open a browser for alphaXiv login, then capture and validate a bearer token."""
    browser_profile = get_browser_profile_path()
    browser_profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    access_token = _extract_access_token_from_browser_profile(headless=False, interactive=True)

    if not access_token:
        raise RuntimeError(
            "Login completed, but no alphaXiv access token was available in the browser session."
        )

    user_payload = fetch_current_user(access_token)
    return build_saved_browser_auth(access_token, user=user_payload, source="browser_login")


def _extract_access_token_for_refresh() -> str | None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _extract_access_token_from_browser_profile(headless=True)
    return cast(
        str | None,
        _run_in_thread(lambda: _extract_access_token_from_browser_profile(headless=True)),
    )


def _extract_access_token_from_browser_profile(
    *,
    headless: bool,
    interactive: bool = False,
) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run 'uv sync --extra browser' and "
            "'uv run playwright install chromium' first."
        ) from exc

    browser_profile = get_browser_profile_path()
    with _windows_playwright_event_loop(), sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(browser_profile),
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--password-store=basic",
            ],
            ignore_default_args=["--enable-automation"],
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.alphaxiv.org/signin", wait_until="load")
            if interactive:
                input("[Press ENTER after completing the alphaXiv sign-in flow] ")
            page.goto("https://www.alphaxiv.org/", wait_until="domcontentloaded")
            return _extract_access_token(page)
        finally:
            context.close()


def _extract_access_token(page: Any) -> str | None:
    script = """
    async () => {
      const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
      const keys = [
        "alphaxiv_client_api_key",
        "alphaxiv_client_api_key_original",
        "alphaxiv_client_api_key_impersonation",
      ];
      const readStoredToken = () => {
        for (const key of keys) {
          const value = window.localStorage.getItem(key);
          if (value) {
            return value;
          }
        }
        return null;
      };

      for (let attempt = 0; attempt < 40; attempt += 1) {
        const storedToken = readStoredToken();
        if (storedToken) {
          return storedToken;
        }

        if (window.Clerk?.loaded && window.Clerk.session) {
          const clerkToken = await window.Clerk.session.getToken();
          if (clerkToken) {
            return clerkToken;
          }
        }

        await sleep(250);
      }

      return null;
    }
    """
    token = page.evaluate(script)
    if isinstance(token, str) and token.strip():
        return token.strip()
    return None


def _run_in_thread(func: Callable[[], Any]) -> Any:
    result: dict[str, Any] = {}
    error: dict[str, BaseException] = {}

    def _target() -> None:
        try:
            result["value"] = func()
        except BaseException as exc:  # pragma: no cover - forwarded immediately
            error["value"] = exc

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join()
    if "value" in error:
        raise error["value"]
    return result.get("value")


@contextmanager
def _windows_playwright_event_loop() -> Iterator[None]:
    if sys.platform != "win32":
        yield
        return

    original_policy = asyncio.get_event_loop_policy()
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    try:
        yield
    finally:
        asyncio.set_event_loop_policy(original_policy)
