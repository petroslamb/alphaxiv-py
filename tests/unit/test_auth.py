from __future__ import annotations

from datetime import UTC, datetime

from alphaxiv import auth
from alphaxiv.auth import (
    ALPHAXIV_API_KEY_ENV,
    authenticate_with_api_key,
    build_saved_api_key,
    clear_saved_api_key,
    load_api_key_value,
    load_saved_api_key,
    resolve_api_key,
    save_api_key,
)
from alphaxiv.paths import get_api_key_path


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


def test_clear_saved_api_key_removes_saved_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_api_key(build_saved_api_key("axv1_test-token"))

    clear_saved_api_key()

    assert not get_api_key_path().exists()


def test_resolve_api_key_uses_env_first(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_api_key(build_saved_api_key("axv1_saved-token"))
    monkeypatch.setenv(ALPHAXIV_API_KEY_ENV, "axv1_env-token")

    saved_api_key = resolve_api_key()

    assert saved_api_key is not None
    assert saved_api_key.api_key == "axv1_env-token"
    assert saved_api_key.source == "env"
    assert load_api_key_value() == "axv1_env-token"


def test_authenticate_with_api_key_validates_and_returns_saved_api_key(monkeypatch) -> None:
    monkeypatch.setattr(
        auth, "fetch_current_user", lambda _token, timeout=30.0: {"email": "petros@example.com"}
    )

    saved_api_key = authenticate_with_api_key("Bearer axv1_test-token")

    assert saved_api_key.api_key == "axv1_test-token"
    assert saved_api_key.source == "saved"
    assert saved_api_key.email == "petros@example.com"
