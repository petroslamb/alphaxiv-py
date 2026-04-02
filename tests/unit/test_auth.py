from __future__ import annotations

from datetime import UTC, datetime

from alphaxiv import auth
from alphaxiv.auth import (
    ALPHAXIV_API_KEY_ENV,
    SavedBrowserAuth,
    authenticate_with_api_key,
    build_saved_api_key,
    build_saved_browser_auth,
    clear_saved_api_key,
    clear_saved_browser_auth,
    ensure_saved_browser_auth,
    load_api_key_value,
    load_saved_api_key,
    load_saved_browser_auth,
    resolve_api_key,
    save_api_key,
    save_browser_auth,
)
from alphaxiv.paths import get_api_key_path, get_browser_auth_path, get_browser_profile_path


def test_build_saved_api_key_normalizes_prefix_and_exposes_metadata() -> None:
    saved_api_key = build_saved_api_key(
        "Bearer axv1_8f92dff095b1_edac2199",
        user={"name": "Petros", "email": "petros@example.com"},
        saved_at=datetime(2026, 3, 12, 9, 0, tzinfo=UTC),
    )

    assert saved_api_key.api_key == "axv1_8f92dff095b1_edac2199"
    assert saved_api_key.authorization_header == "Bearer axv1_8f92dff095b1_edac2199"
    assert saved_api_key.key_prefix == "axv1_8f92dff095b1"
    assert saved_api_key.display_name == "Petros"
    assert saved_api_key.email == "petros@example.com"


def test_save_and_load_api_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    saved_api_key = build_saved_api_key(
        "axv1_test-token",
        user={"username": "petros", "email": "petros@example.com"},
        saved_at=datetime(2026, 3, 12, 9, 0, tzinfo=UTC),
    )

    save_api_key(saved_api_key)
    loaded = load_saved_api_key()

    assert loaded is not None
    assert loaded.api_key == "axv1_test-token"
    assert loaded.display_name == "petros"
    assert loaded.saved_at == datetime(2026, 3, 12, 9, 0, tzinfo=UTC)
    assert get_api_key_path().exists()


def test_build_saved_browser_auth_normalizes_prefix_and_exposes_metadata() -> None:
    saved_auth = build_saved_browser_auth(
        "Bearer browser-session-token",
        user={"name": "Petros", "email": "petros@example.com"},
        created_at=datetime(2026, 3, 12, 9, 0, tzinfo=UTC),
    )

    assert saved_auth.access_token == "browser-session-token"
    assert saved_auth.authorization_header == "Bearer browser-session-token"
    assert saved_auth.token_prefix == "browser-sess"
    assert saved_auth.display_name == "Petros"
    assert saved_auth.email == "petros@example.com"


def test_save_and_load_browser_auth(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    saved_auth = build_saved_browser_auth(
        "browser-session-token",
        user={"username": "petros", "email": "petros@example.com"},
        created_at=datetime(2026, 3, 12, 9, 0, tzinfo=UTC),
    )

    save_browser_auth(saved_auth)
    loaded = load_saved_browser_auth()

    assert loaded is not None
    assert loaded.access_token == "browser-session-token"
    assert loaded.display_name == "petros"
    assert loaded.created_at == datetime(2026, 3, 12, 9, 0, tzinfo=UTC)
    assert get_browser_auth_path().exists()


def test_clear_saved_api_key_removes_saved_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_api_key(build_saved_api_key("axv1_test-token"))

    clear_saved_api_key()

    assert not get_api_key_path().exists()


def test_clear_saved_browser_auth_removes_saved_token_and_profile(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_browser_auth(build_saved_browser_auth("browser-session-token"))
    browser_profile = get_browser_profile_path()
    browser_profile.mkdir(parents=True, exist_ok=True)

    clear_saved_browser_auth(clear_browser_profile=True)

    assert not get_browser_auth_path().exists()
    assert not browser_profile.exists()


def test_resolve_api_key_uses_env_first(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_api_key(build_saved_api_key("axv1_saved-token"))
    monkeypatch.setenv(ALPHAXIV_API_KEY_ENV, "axv1_env-token")

    saved_api_key = resolve_api_key()

    assert saved_api_key is not None
    assert saved_api_key.api_key == "axv1_env-token"
    assert saved_api_key.source == "env"
    assert load_api_key_value() == "axv1_env-token"


def test_ensure_saved_browser_auth_refreshes_expired_token(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    expired_auth = SavedBrowserAuth(
        access_token="expired-token",
        created_at=datetime(2026, 3, 11, 9, 0, tzinfo=UTC),
        expires_at=datetime(2026, 3, 11, 10, 0, tzinfo=UTC),
        user={"email": "old@example.com"},
    )
    refreshed_auth = build_saved_browser_auth(
        "refreshed-token",
        user={"email": "new@example.com"},
        created_at=datetime(2026, 3, 12, 9, 0, tzinfo=UTC),
    )
    save_browser_auth(expired_auth)
    monkeypatch.setattr(auth, "refresh_saved_browser_auth", lambda timeout=30.0: refreshed_auth)

    saved_auth = ensure_saved_browser_auth()

    assert saved_auth == refreshed_auth


def test_authenticate_with_api_key_validates_and_returns_saved_api_key(monkeypatch) -> None:
    monkeypatch.setattr(
        auth, "fetch_current_user", lambda _token, timeout=30.0: {"email": "petros@example.com"}
    )

    saved_api_key = authenticate_with_api_key("Bearer axv1_test-token")

    assert saved_api_key.api_key == "axv1_test-token"
    assert saved_api_key.source == "saved"
    assert saved_api_key.email == "petros@example.com"
