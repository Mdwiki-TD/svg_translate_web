"""Tests for build_engine_options (web pool vs CLI NullPool)."""

from __future__ import annotations

import pytest
from sqlalchemy.pool import NullPool
from src.main_app.config.flask_config import TestingConfig, build_engine_options

MYSQL_URI = "mysql+pymysql://user:pass@localhost/db"
MARIADB_URI = "mariadb+pymysql://user:pass@localhost/db"


def test_web_uses_a_pool_with_pre_ping() -> None:
    opts = build_engine_options(MYSQL_URI, cli=False)

    assert opts["pool_pre_ping"] is True
    assert opts["pool_size"] == 4
    assert opts["max_overflow"] == 2
    assert opts["pool_recycle"] == 280
    assert "poolclass" not in opts


def test_cli_uses_null_pool_without_pool_options() -> None:
    opts = build_engine_options(MYSQL_URI, cli=True)

    assert opts["poolclass"] is NullPool
    for key in ("pool_size", "max_overflow", "pool_recycle", "pool_timeout", "pool_use_lifo", "pool_pre_ping"):
        assert key not in opts  # NullPool rejects these


def test_cli_and_web_share_connect_args() -> None:
    cli_args = build_engine_options(MYSQL_URI, cli=True)["connect_args"]
    web_args = build_engine_options(MYSQL_URI, cli=False)["connect_args"]

    assert cli_args == web_args
    assert cli_args["charset"] == "utf8mb4"


@pytest.mark.parametrize("cli", [True, False])
def test_mariadb_is_treated_like_mysql(cli: bool) -> None:
    assert build_engine_options(MARIADB_URI, cli=cli) == build_engine_options(MYSQL_URI, cli=cli)


@pytest.mark.parametrize("uri", ["sqlite:///:memory:", ""])
@pytest.mark.parametrize("cli", [True, False])
def test_non_mysql_gets_no_options(uri: str, cli: bool) -> None:
    assert build_engine_options(uri, cli=cli) == {}


def test_testing_config_has_no_engine_options() -> None:
    assert TestingConfig.SQLALCHEMY_ENGINE_OPTIONS == {}
