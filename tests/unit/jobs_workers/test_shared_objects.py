"""
Unit tests for shared_objects.py module.

Classes to test: UpdaterOutcome, Summary, SharedworkerObject

"""

from __future__ import annotations

import pytest

from src.main_app.jobs_workers.base_worker_object import WorkerObject
from src.main_app.jobs_workers.shared_objects import (
    SharedworkerObject,
    Summary,
    UpdaterOutcome,
)


class TestUpdaterOutcome:
    def test_create_with_defaults(self):
        o = UpdaterOutcome(kind="skipped")
        assert o.kind == "skipped"
        assert o.newrevid == 0
        assert o.msg == ""

    def test_frozen(self):
        o = UpdaterOutcome(kind="changed")
        with pytest.raises(AttributeError):
            o.kind = "error"

    def test_to_json(self):
        o = UpdaterOutcome(kind="missing", msg="not found")
        d = o.to_json()
        assert d["kind"] == "missing"
        assert d["msg"] == "not found"

    def test_all_kind_values(self):
        for kind in ("missing", "skipped", "changed", "error"):
            o = UpdaterOutcome(kind=kind)
            assert o.kind == kind


class TestSummary:
    def test_defaults(self):
        s = Summary()
        assert s.processed == 0
        assert s.total == 0

    def test_not_frozen(self):
        s = Summary()
        s.processed = 10
        s.total = 20
        assert s.processed == 10
        assert s.total == 20


class TestSharedworkerObject:
    def test_inherits_worker_object(self):
        obj = SharedworkerObject()
        assert isinstance(obj, WorkerObject)

    def test_default_lists_are_empty(self):
        obj = SharedworkerObject()
        assert obj.pages_processed == []
        assert obj.pages_changed == []
        assert obj.pages_errors == []
        assert obj.pages_skipped == []
        assert obj.pages_missing == []

    def test_default_summary(self):
        obj = SharedworkerObject()
        assert obj.summary.processed == 0
        assert obj.summary.total == 0

    def test_lists_are_independent(self):
        a = SharedworkerObject()
        b = SharedworkerObject()
        a.pages_changed.append({"title": "Test"})
        assert b.pages_changed == []

    def test_to_json(self):
        obj = SharedworkerObject(status="running")
        d = obj.to_json()
        assert d["status"] == "running"
        assert "summary" in d
        assert "pages_processed" in d
