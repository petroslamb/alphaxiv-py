from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import Mapping
from datetime import UTC, datetime

from alphaxiv import auth
from alphaxiv.auth import (
    ALPHAXIV_API_KEY_ENV,
    authenticate_with_api_key,
    build_saved_auth,
    clear_saved_auth,
    ensure_saved_auth,
    load_authorization,
    load_saved_auth,
    save_auth,
)
from alphaxiv.paths import get_auth_path, get_browser_profile_path


def _make_jwt(expiry_timestamp: int) -> str:
    header = {"alg": "none", "typ": "JWT"}
    payload = {"exp": expiry_timestamp}

    def _encode(part: Mapping[str, object]) -> str:
        encoded = base64.urlsafe_b64encode(json.dumps(part).encode("utf-8")).decode("utf-8")
        return encoded.rstrip("=")

    return f"{_encode(header)}.{_encode(payload)}.signature"


def test_build_saved_auth_decodes_jwt_expiry() -> None:
    saved_auth = build_saved_auth(
        _make_jwt(1_900_000_000),
        user={"name": "Petros", "email": "petros@example.com"},
    )

    assert saved_auth.display_name == "Petros"
    assert saved_auth.email == "petros@example.com"
    assert saved_auth.authorization_header.startswith("Bearer ")
    assert saved_auth.expires_at == datetime.fromtimestamp(1_900_000_000, tz=UTC)


def test_save_and_load_auth(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    saved_auth = build_saved_auth(
        "test-token",
        user={"username": "petros", "email": "petros@example.com"},
    )

    save_auth(saved_auth)
    loaded = load_saved_auth()

    assert loaded is not None
    assert loaded.access_token == "test-token"
    assert loaded.display_name == "petros"
    assert load_authorization() == "Bearer test-token"
    assert get_auth_path().exists()


def test_clear_saved_auth_removes_browser_profile(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_auth(build_saved_auth("test-token"))
    browser_profile = get_browser_profile_path()
    browser_profile.mkdir(parents=True, exist_ok=True)
    (browser_profile / "marker.txt").write_text("profile")

    clear_saved_auth(clear_browser_profile=True)

    assert not get_auth_path().exists()
    assert not browser_profile.exists()


def test_ensure_saved_auth_returns_expired_saved_auth_without_refresh(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    expired_auth = build_saved_auth(
        _make_jwt(1_700_000_000),
        user={"email": "stale@example.com"},
    )
    save_auth(expired_auth)

    active_auth = ensure_saved_auth()

    assert active_auth is not None
    assert active_auth.email == "stale@example.com"
    assert active_auth.is_expired


def test_load_authorization_uses_env_api_key_first(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_auth(build_saved_auth("saved-token"))
    monkeypatch.setenv(ALPHAXIV_API_KEY_ENV, "axv1_env-token")

    async def _load() -> str | None:
        return load_authorization()

    authorization = asyncio.run(_load())

    assert authorization == "Bearer axv1_env-token"


def test_authenticate_with_api_key_validates_and_marks_kind(monkeypatch) -> None:
    monkeypatch.setattr(
        auth, "fetch_current_user", lambda _token, timeout=30.0: {"email": "petros@example.com"}
    )

    saved_auth = authenticate_with_api_key("Bearer axv1_test-token")

    assert saved_auth.access_token == "axv1_test-token"
    assert saved_auth.kind == "api_key"
    assert saved_auth.source == "saved"
    assert saved_auth.email == "petros@example.com"
