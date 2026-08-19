from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.api_services.clients.wiki_client import (
    coerce_encrypted,
    get_user_groups,
    get_user_site,
)
from src.main_app.services.core.crypto import encrypt_value


class TestCoerceEncrypted:
    def test_coerce_encrypted(self) -> None:
        assert coerce_encrypted(b"bytes") == b"bytes"
        assert coerce_encrypted(bytearray(b"array")) == b"array"
        assert coerce_encrypted(memoryview(b"view")) == b"view"
        assert coerce_encrypted("string") == b"string"
        assert coerce_encrypted(None) is None
        assert coerce_encrypted(123) is None

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
        calls: list[Any] = []

        class DummySite:
            def __init__(self, host: str, **kwargs: object) -> None:
                calls.append({"host": host, **kwargs})

        monkeypatch.setattr("src.main_app.api_services.clients.wiki_client.Site", DummySite)

        user = {
            "access_token": encrypt_value("my-access-key"),
            "access_secret": encrypt_value("my-access-secret"),
        }
        site = get_user_site(user)

        assert site is not None
        assert len(calls) == 1
        assert calls[0]["host"] in ["commons.wikimedia.org", "test.wikipedia.org"]

    def test_get_user_site_build_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_error(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Build failed")

        monkeypatch.setattr(
            "src.main_app.api_services.clients.wiki_client.Site",
            raise_error,
        )

        user = {
            "access_token": encrypt_value("token"),
            "access_secret": encrypt_value("secret"),
        }
        site = get_user_site(user)

        assert site is None


class TestGetUserGroups:
    def test_returns_casefolded_groups(self, monkeypatch: pytest.MonkeyPatch) -> None:
        site = MagicMock()
        site.get.return_value = {
            "query": {"userinfo": {"groups": ["*", "User", "autopatrolled"]}}
        }
        monkeypatch.setattr(
            "src.main_app.api_services.clients.wiki_client.get_user_site",
            lambda user: site,
        )

        groups = get_user_groups({"access_token": b"token", "access_secret": b"secret"})

        assert groups == frozenset({"*", "user", "autopatrolled"})
        site.get.assert_called_once_with("query", meta="userinfo", uiprop="groups")

    def test_returns_empty_group_set_for_user_without_groups(self, monkeypatch: pytest.MonkeyPatch) -> None:
        site = MagicMock()
        site.get.return_value = {"query": {"userinfo": {"groups": []}}}
        monkeypatch.setattr(
            "src.main_app.api_services.clients.wiki_client.get_user_site",
            lambda user: site,
        )

        assert get_user_groups({"access_token": b"token", "access_secret": b"secret"}) == frozenset()

    def test_returns_none_when_oauth_site_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.api_services.clients.wiki_client.get_user_site",
            lambda user: None,
        )

        assert get_user_groups({"access_token": b"token", "access_secret": b"secret"}) is None

    def test_returns_none_for_missing_groups_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        site = MagicMock()
        site.get.return_value = {"query": {"userinfo": {}}}
        monkeypatch.setattr(
            "src.main_app.api_services.clients.wiki_client.get_user_site",
            lambda user: site,
        )

        assert get_user_groups({"access_token": b"token", "access_secret": b"secret"}) is None

    def test_returns_none_when_mediawiki_request_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        site = MagicMock()
        site.get.side_effect = RuntimeError("MediaWiki unavailable")
        monkeypatch.setattr(
            "src.main_app.api_services.clients.wiki_client.get_user_site",
            lambda user: site,
        )

        assert get_user_groups({"access_token": b"token", "access_secret": b"secret"}) is None


@patch("src.main_app.api_services.clients.wiki_client.settings")
@patch("src.main_app.api_services.clients.wiki_client.Site")
@patch("src.main_app.api_services.clients.wiki_client.decrypt_value")
def test_get_user_site(mock_decrypt, mock_site, mock_settings, mock_app):
    mock_settings.oauth = MagicMock()
    mock_settings.other = MagicMock()
    mock_decrypt.side_effect = lambda x: x.decode() if isinstance(x, bytes) else x

    user = {"access_token": b"token", "access_secret": b"secret"}

    site = get_user_site(user)
    assert site is not None
    mock_site.assert_called_once()


def test_get_user_site_no_user():
    assert get_user_site(None) is None


def test_get_user_site_no_tokens():
    assert get_user_site({}) is None
