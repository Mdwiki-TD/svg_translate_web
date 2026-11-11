"""Unit tests for OAuth mwclient site builder (no network)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from src.main_app.api_services.clients.wikisite_client import (
    WikiSiteClient,
    coerce_encrypted,
)
from src.main_app.services.core.crypto import CryptoService


class TestCoerceEncrypted:
    def test_coerce_encrypted(self) -> None:
        assert coerce_encrypted(b"bytes") == b"bytes"
        assert coerce_encrypted(bytearray(b"array")) == b"array"
        assert coerce_encrypted(memoryview(b"view")) == b"view"
        assert coerce_encrypted("string") == b"string"
        assert coerce_encrypted(None) is None
        assert coerce_encrypted(123) is None
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
        assert WikiSiteClient.get_user_site("test.wikipedia.org", None) is None

    def test_get_user_site_missing_access_token(self) -> None:
        user = {"access_secret": b"secret"}
        assert WikiSiteClient.get_user_site("test.wikipedia.org", user) is None

    def test_get_user_site_missing_access_secret(self) -> None:
        user = {"access_token": b"token"}
        assert WikiSiteClient.get_user_site("test.wikipedia.org", user) is None

    def test_get_user_site_empty_tokens(self) -> None:
        user = {"access_token": b"", "access_secret": b"secret"}
        assert WikiSiteClient.get_user_site("test.wikipedia.org", user) is None

    def test_get_user_site_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[Any] = []

        class DummySite:
            def __init__(self, host: str, **kwargs: object) -> None:
                calls.append({"host": host, **kwargs})
                self.username = "username"
                self.rights = ["edit"]

        monkeypatch.setattr("src.main_app.api_services.clients.wikisite_client.Site", DummySite)

        user = {
            "access_token": CryptoService().encrypt("my-access-key"),
            "access_secret": CryptoService().encrypt("my-access-secret"),
        }
        site = WikiSiteClient.get_user_site("test.wikipedia.org", user)

        assert site is not None
        assert len(calls) == 1
        assert calls[0]["host"] in ["commons.wikimedia.org", "test.wikipedia.org"]

    def test_get_user_site_build_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_error(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Build failed")

        monkeypatch.setattr(
            "src.main_app.api_services.clients.wikisite_client.Site",
            raise_error,
        )

        user = {
            "access_token": CryptoService().encrypt("token"),
            "access_secret": CryptoService().encrypt("secret"),
        }
        site = WikiSiteClient.get_user_site("test.wikipedia.org", user)

        assert site is None


@patch("src.main_app.api_services.clients.wikisite_client.get_settings")
@patch("src.main_app.api_services.clients.wikisite_client.Site")
@patch("src.main_app.api_services.clients.wikisite_client.CryptoService.decrypt")
def test_get_user_site(mock_decrypt, mock_site, mock_settings, mock_app):
    mock_settings.oauth = MagicMock()
    mock_settings.other = MagicMock()
    mock_decrypt.side_effect = lambda x: x.decode() if isinstance(x, bytes) else x

    user = {"access_token": b"token", "access_secret": b"secret"}

    site = WikiSiteClient.get_user_site("test.wikipedia.org", user)
    assert site is not None
    mock_site.assert_called_once()


def test_get_user_site_no_user():
    assert WikiSiteClient.get_user_site("test.wikipedia.org", None) is None


def test_get_user_site_no_tokens():
    assert WikiSiteClient.get_user_site("test.wikipedia.org", {}) is None
