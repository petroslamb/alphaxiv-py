"""Saved auth and browser-assisted login helpers."""

from __future__ import annotations

import asyncio
import base64
import json
import shutil
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from ._core import BASE_API_URL, DEFAULT_TIMEOUT, USER_AGENT
from .exceptions import APIError
from .paths import ensure_home_path, get_auth_path, get_browser_profile_path

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
        return datetime.fromtimestamp(exp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


@dataclass(slots=True)
class SavedAuth:
    """Locally persisted alphaXiv bearer auth."""

    access_token: str
    created_at: datetime
    expires_at: datetime | None = None
    user: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def authorization_header(self) -> str:
        return f"Bearer {self.access_token}"

    @property
    def user_id(self) -> str | None:
        return _coalesce_string(
            self.user.get("id"),
            self.user.get("user_id"),
            self.user.get("userId"),
            _nested_get(self.user, "user", "id"),
        )

    @property
    def display_name(self) -> str | None:
        return _coalesce_string(
            self.user.get("name"),
            self.user.get("full_name"),
            self.user.get("fullName"),
            self.user.get("username"),
            self.user.get("handle"),
            _nested_get(self.user, "user", "name"),
            _nested_get(self.user, "user", "full_name"),
            _nested_get(self.user, "user", "username"),
        )

    @property
    def email(self) -> str | None:
        email_addresses = self.user.get("email_addresses")
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
            self.user.get("email"),
            self.user.get("email_address"),
            self.user.get("primary_email"),
            primary_email,
            _nested_get(self.user, "user", "email"),
        )

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "user": self.user,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SavedAuth":
        created_at = payload.get("created_at")
        expires_at = payload.get("expires_at")
        return cls(
            access_token=str(payload.get("access_token", "")),
            created_at=_parse_iso_datetime(created_at) or datetime.now(timezone.utc),
            expires_at=_parse_iso_datetime(expires_at),
            user=payload.get("user") if isinstance(payload.get("user"), dict) else {},
        )


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_saved_auth(path: Path | None = None) -> SavedAuth | None:
    """Load the locally saved auth token, if present."""
    auth_path = path or get_auth_path()
    if not auth_path.exists():
        return None
    try:
        payload = json.loads(auth_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or not payload.get("access_token"):
        return None
    return SavedAuth.from_dict(payload)


def load_authorization() -> str | None:
    """Load the saved Authorization header value, if present."""
    saved_auth = ensure_saved_auth()
    if not saved_auth:
        return None
    return saved_auth.authorization_header


def save_auth(saved_auth: SavedAuth, path: Path | None = None) -> Path:
    """Persist auth to disk with owner-only permissions."""
    ensure_home_path()
    auth_path = path or get_auth_path()
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(json.dumps(saved_auth.to_dict(), indent=2))
    auth_path.chmod(0o600)
    return auth_path


def ensure_saved_auth(timeout: float = DEFAULT_TIMEOUT) -> SavedAuth | None:
    """Load auth from disk and refresh it from the browser profile when needed."""
    saved_auth = load_saved_auth()
    if saved_auth and not saved_auth.is_expired:
        return saved_auth
    refreshed_auth = refresh_saved_auth(timeout=timeout)
    return refreshed_auth or saved_auth


def clear_saved_auth(*, path: Path | None = None, clear_browser_profile: bool = False) -> None:
    """Remove the saved auth token and optionally the browser profile."""
    auth_path = path or get_auth_path()
    if auth_path.exists():
        auth_path.unlink()
    if clear_browser_profile:
        profile_path = get_browser_profile_path()
        if profile_path.exists():
            shutil.rmtree(profile_path)


def fetch_current_user(access_token: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Validate a bearer token against alphaXiv's authenticated user endpoint."""
    headers = {
        "Authorization": f"Bearer {access_token}",
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


def build_saved_auth(access_token: str, *, user: dict[str, Any] | None = None) -> SavedAuth:
    """Construct a SavedAuth instance from a bearer token."""
    return SavedAuth(
        access_token=access_token,
        created_at=datetime.now(timezone.utc),
        expires_at=_decode_token_expiry(access_token),
        user=user or {},
    )


def refresh_saved_auth(timeout: float = DEFAULT_TIMEOUT) -> SavedAuth | None:
    """Refresh the saved Clerk token from the persistent browser profile."""
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
    saved_auth = build_saved_auth(access_token, user=user_payload)
    save_auth(saved_auth)
    return saved_auth


def authenticate_with_browser() -> SavedAuth:
    """Open a browser for alphaXiv login, then capture and validate a bearer token."""
    browser_profile = get_browser_profile_path()
    browser_profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    access_token = _extract_access_token_from_browser_profile(headless=False, interactive=True)

    if not access_token:
        raise RuntimeError(
            "Login completed, but no alphaXiv access token was available in the browser session."
        )

    user_payload = fetch_current_user(access_token)
    return build_saved_auth(access_token, user=user_payload)


def _extract_access_token_for_refresh() -> str | None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _extract_access_token_from_browser_profile(headless=True)
    return _run_in_thread(lambda: _extract_access_token_from_browser_profile(headless=True))


def _extract_access_token_from_browser_profile(
    *, headless: bool, interactive: bool = False
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


def _run_in_thread(func):
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
