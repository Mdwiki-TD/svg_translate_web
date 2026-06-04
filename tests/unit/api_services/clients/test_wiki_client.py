"""Unit tests for OAuth mwclient site builder (no network)."""

import pytest

from src.main_app.api_services.clients.wiki_client import (
    coerce_encrypted,
    get_user_site,
)
from src.main_app.core.crypto import encrypt_value


class TestCoerceEncrypted:
    def test_coerce_encrypted_none(self) -> None:
        assert coerce_encrypted(None) is None

    def test_coerce_encrypted_bytes(self) -> None:
        result = coerce_encrypted(b"test-bytes")
        assert result == b"test-bytes"

    def test_coerce_encrypted_bytearray(self) -> None:
        result = coerce_encrypted(bytearray(b"test-bytearray"))
        assert result == b"test-bytearray"

    def test_coerce_encrypted_memoryview(self) -> None:
        result = coerce_encrypted(memoryview(b"test-memoryview"))
        assert result == b"test-memoryview"

    def test_coerce_encrypted_str(self) -> None:
        result = coerce_encrypted("test-string")
        assert result == b"test-string"

    def test_coerce_encrypted_invalid_type(self) -> None:
        result = coerce_encrypted(12345)
        assert result is None

    def test_coerce_encrypted_list(self) -> None:
        result = coerce_encrypted([1, 2, 3])
        assert result is None


class TestGetUserSite:
    def test_get_user_site_none_user(self) -> None:
        assert get_user_site(None) is None

    def test_get_user_site_missing_access_token(self) -> None:
        user = {"access_secret": b"secret"}
        assert get_user_site(user) is None

    def test_get_user_site_missing_access_secret(self) -> None:
        user = {"access_token": b"token"}
        assert get_user_site(user) is None

    def test_get_user_site_empty_tokens(self) -> None:
        user = {"access_token": b"", "access_secret": b"secret"}
        assert get_user_site(user) is None

    def test_get_user_site_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls = []

        class DummySite:
            def __init__(self, host: str, **kwargs: object) -> None:
                calls.append({"host": host, **kwargs})

        monkeypatch.setattr("src.main_app.api_services.clients.wiki_client.mwclient.Site", DummySite)

        user = {
            "access_token": encrypt_value("my-access-key"),
            "access_secret": encrypt_value("my-access-secret"),
        }
        site = get_user_site(user)

        assert site is not None
        assert len(calls) == 1
        assert calls[0]["host"] == "commons.wikimedia.org"

    def test_get_user_site_build_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_error(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Build failed")

        monkeypatch.setattr(
            "src.main_app.api_services.clients.wiki_client.mwclient.Site",
            raise_error,
        )

        user = {
            "access_token": encrypt_value("token"),
            "access_secret": encrypt_value("secret"),
        }
        site = get_user_site(user)

        assert site is None
