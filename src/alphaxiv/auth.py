"""API-key loading, validation, and persistence helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from ._core import BASE_API_URL, DEFAULT_TIMEOUT, USER_AGENT
from .exceptions import APIError
from .paths import ensure_home_path, get_api_key_path

ALPHAXIV_API_KEY_ENV = "ALPHAXIV_API_KEY"


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


def _normalize_api_key(secret: str) -> str:
    cleaned = secret.strip()
    if cleaned.lower().startswith("bearer "):
        return cleaned[7:].strip()
    return cleaned


def _looks_like_api_key(secret: str) -> bool:
    return secret.startswith("axv1_")


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


def clear_saved_api_key(*, path: Path | None = None) -> None:
    """Remove the saved API key."""
    api_key_path = path or get_api_key_path()
    if api_key_path.exists():
        api_key_path.unlink()


def fetch_current_user(api_key: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Validate an API key against alphaXiv's authenticated user endpoint."""
    headers = {
        "Authorization": f"Bearer {_normalize_api_key(api_key)}",
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
