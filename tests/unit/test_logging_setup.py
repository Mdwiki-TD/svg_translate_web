"""Tests for DailyFileHandler (multi-process safe daily log files)."""

from __future__ import annotations

import logging
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from src import logging_setup
from src.logging_setup import DailyFileHandler, ProcessLoggingConfigurator

SRC_DIR = str(Path(logging_setup.__file__).parent)


def _record(msg: str) -> logging.LogRecord:
    return logging.LogRecord("t", logging.INFO, __file__, 1, msg, None, None)


@pytest.fixture
def fake_day(monkeypatch):
    """Control the 'current' UTC day seen by DailyFileHandler."""
    state = {"day": "2024-01-15"}
    monkeypatch.setattr(DailyFileHandler, "_today", staticmethod(lambda: state["day"]))
    return state


def test_writes_to_dated_file(tmp_path, fake_day):
    handler = DailyFileHandler(tmp_path, "app")
    handler.handle(_record("hello"))
    handler.close()

    assert not (tmp_path / "app.log").exists()
    assert "hello" in (tmp_path / "app.2024-01-15.log").read_text()


def test_file_is_created_lazily(tmp_path, fake_day):
    handler = DailyFileHandler(tmp_path, "app")
    assert list(tmp_path.iterdir()) == []
    handler.close()


def test_switches_file_when_day_changes(tmp_path, fake_day):
    handler = DailyFileHandler(tmp_path, "app")
    handler.handle(_record("day one"))
    fake_day["day"] = "2024-01-16"
    handler.handle(_record("day two"))
    handler.close()

    assert (tmp_path / "app.2024-01-15.log").read_text().count("day one") == 1
    assert "day two" not in (tmp_path / "app.2024-01-15.log").read_text()
    assert "day two" in (tmp_path / "app.2024-01-16.log").read_text()


def test_keeps_only_newest_backup_count_files(tmp_path, fake_day):
    for day in range(1, 11):
        (tmp_path / f"app.2023-12-{day:02d}.log").write_text("old")
    (tmp_path / "errors.2023-12-01.log").write_text("other stem, must survive")

    handler = DailyFileHandler(tmp_path, "app", backup_count=3)
    handler.close()

    remaining = sorted(p.name for p in tmp_path.glob("app.*.log"))
    assert remaining == ["app.2023-12-08.log", "app.2023-12-09.log", "app.2023-12-10.log"]
    assert (tmp_path / "errors.2023-12-01.log").exists()


def test_production_uses_daily_handler_and_dev_uses_watched(tmp_path):
    prod = ProcessLoggingConfigurator.build_file_handler(tmp_path / "app.log", logging.INFO, daily_rotation=True)
    dev = ProcessLoggingConfigurator.build_file_handler(tmp_path / "app.log", logging.INFO, daily_rotation=False)
    try:
        assert isinstance(prod, DailyFileHandler)
        assert not isinstance(dev, DailyFileHandler)
    finally:
        prod.close()
        dev.close()


CHILD = textwrap.dedent("""
    import logging, os, sys
    sys.path.insert(0, {src!r})
    from logging_setup import DailyFileHandler

    PER_DAY = {per_day}
    calls = {{"n": 0}}

    def fake_today():
        calls["n"] += 1
        return "2024-01-15" if calls["n"] <= PER_DAY else "2024-01-16"

    DailyFileHandler._today = staticmethod(fake_today)

    handler = DailyFileHandler({directory!r}, "app")
    calls["n"] = 0  # __init__ already consumed one call; start counting at the first emit
    handler.setFormatter(logging.Formatter("%(message)s"))
    pid = os.getpid()
    for i in range(PER_DAY * 2):
        handler.handle(logging.LogRecord("t", logging.INFO, "f", 1, f"{{pid}}-{{i}}-" + "x" * 300, None, None))
    handler.close()
    """)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows emulates O_APPEND with seek+write, which is not atomic across processes; "
    "DailyFileHandler's multi-process guarantee relies on POSIX append semantics (production is Linux)",
)
def test_several_processes_share_files_without_losing_or_mixing_lines(tmp_path):
    workers, per_day = 4, 500
    script = CHILD.format(src=SRC_DIR, per_day=per_day, directory=str(tmp_path))

    procs = [subprocess.Popen([sys.executable, "-c", script]) for _ in range(workers)]
    assert all(p.wait(timeout=60) == 0 for p in procs)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["app.2024-01-15.log", "app.2024-01-16.log"]
    line_re = re.compile(r"^\d+-\d+-x{300}$")
    for name in ("app.2024-01-15.log", "app.2024-01-16.log"):
        lines = (tmp_path / name).read_text().splitlines()
        assert len(lines) == workers * per_day  # nothing lost
        assert all(line_re.match(line) for line in lines)  # nothing interleaved


@pytest.mark.parametrize("daily", [False, True])
def test_max_level_keeps_errors_out_of_app_log(tmp_path, fake_day, daily):
    app_h = ProcessLoggingConfigurator.build_file_handler(
        tmp_path / "app.log", logging.INFO, daily_rotation=daily, max_level=logging.ERROR
    )
    err_h = ProcessLoggingConfigurator.build_file_handler(tmp_path / "errors.log", logging.ERROR, daily_rotation=daily)
    # A real logger applies the handler levels (Handler.handle() alone does not)
    log = logging.getLogger(f"max_level_test_{daily}")
    log.propagate = False
    log.setLevel(logging.DEBUG)
    log.addHandler(app_h)
    log.addHandler(err_h)
    try:
        log.debug("msg-dbg")
        log.info("msg-inf")
        log.warning("msg-wrn")
        log.error("msg-err")
        log.critical("msg-crt")
    finally:
        log.removeHandler(app_h)
        log.removeHandler(err_h)
        app_h.close()
        err_h.close()

    app_text = "".join(p.read_text() for p in tmp_path.glob("app*.log"))
    err_text = "".join(p.read_text() for p in tmp_path.glob("errors*.log"))
    assert "msg-inf" in app_text and "msg-wrn" in app_text
    assert not any(m in app_text for m in ("msg-dbg", "msg-err", "msg-crt"))
    assert "msg-err" in err_text and "msg-crt" in err_text
    assert not any(m in err_text for m in ("msg-dbg", "msg-inf", "msg-wrn"))
