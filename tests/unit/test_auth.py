from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime, timezone

from alphaxiv import auth
from alphaxiv.auth import build_saved_auth, clear_saved_auth, ensure_saved_auth, load_authorization, load_saved_auth, save_auth
from alphaxiv.paths import get_auth_path, get_browser_profile_path


def _make_jwt(expiry_timestamp: int) -> str:
    header = {"alg": "none", "typ": "JWT"}
    payload = {"exp": expiry_timestamp}

    def _encode(part: dict[str, object]) -> str:
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
    assert saved_auth.expires_at == datetime.fromtimestamp(1_900_000_000, tz=timezone.utc)


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


def test_ensure_saved_auth_refreshes_expired_token(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    expired_auth = build_saved_auth(
        _make_jwt(1_700_000_000),
        user={"email": "stale@example.com"},
    )
    save_auth(expired_auth)
    refreshed_auth = build_saved_auth(
        _make_jwt(1_900_000_000),
        user={"email": "fresh@example.com"},
    )
    monkeypatch.setattr(auth, "refresh_saved_auth", lambda timeout=30.0: refreshed_auth)

    active_auth = ensure_saved_auth()

    assert active_auth is not None
    assert active_auth.email == "fresh@example.com"


def test_load_authorization_refreshes_in_running_event_loop(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    expired_auth = build_saved_auth(
        _make_jwt(1_700_000_000),
        user={"email": "stale@example.com"},
    )
    save_auth(expired_auth)
    get_browser_profile_path().mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(auth, "_extract_access_token_from_browser_profile", lambda **_kwargs: "fresh-token")
    monkeypatch.setattr(auth, "fetch_current_user", lambda _token, timeout=30.0: {"email": "fresh@example.com"})

    async def _load() -> str | None:
        return load_authorization()

    authorization = asyncio.run(_load())

    assert authorization == "Bearer fresh-token"
