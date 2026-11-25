"""Tests for ``backends.backend_registry.BackendRegistry``."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from src.main_app.jobs.backends.backend_registry import BackendRegistry
from src.main_app.jobs.backends.base import JobBackend
from src.main_app.jobs.backends.thread_backend import ThreadBackend
from src.main_app.jobs.backends.toolforge_backend import ToolforgeBackend

MODULE = "src.main_app.jobs.backends.backend_registry"


@pytest.fixture
def mock_get_settings(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock(return_value=SimpleNamespace(jobs=SimpleNamespace(backend="thread")))
    monkeypatch.setattr(f"{MODULE}.get_settings", _mock)
    return _mock


@pytest.fixture
def make_backend_cls() -> type:
    """Factory for tiny concrete backends that are cheap to instantiate."""

    def _factory(name: str = "Fake") -> type[JobBackend]:
        class FakeBackend(JobBackend):
            def start(self, job, job_data, user=None) -> str:
                return name

            def cancel(self, job) -> bool:
                return True

        FakeBackend.__name__ = name
        return FakeBackend

    return _factory


class TestGetBackendName:
    def test_returns_the_configured_backend(self, mock_get_settings: MagicMock) -> None:
        assert BackendRegistry().get_backend_name() == "thread"

    def test_ignores_the_job_type(self, mock_get_settings: MagicMock) -> None:
        mock_get_settings.return_value.jobs.backend = "toolforge"

        assert BackendRegistry().get_backend_name("anything") == "toolforge"


class TestGetBackend:
    def test_returns_an_instance_of_the_registered_class(self, make_backend_cls) -> None:
        registry = BackendRegistry()
        fake_cls = make_backend_cls()
        registry.register("fake", fake_cls)

        assert isinstance(registry.get_backend("fake"), fake_cls)

    def test_defaults_to_the_configured_backend(self, mock_get_settings: MagicMock, make_backend_cls) -> None:
        registry = BackendRegistry()
        fake_cls = make_backend_cls()
        registry.register("thread", fake_cls)

        assert isinstance(registry.get_backend(), fake_cls)

    def test_unknown_backend_lists_the_available_ones(self, make_backend_cls) -> None:
        registry = BackendRegistry()
        registry.register("fake", make_backend_cls())

        with pytest.raises(ValueError, match=r"Unknown job backend: 'nope'.*fake"):
            registry.get_backend("nope")

    def test_returns_a_new_instance_each_time(self, make_backend_cls) -> None:
        registry = BackendRegistry()
        registry.register("fake", make_backend_cls())

        assert registry.get_backend("fake") is not registry.get_backend("fake")


class TestDefaults:
    def test_thread_and_toolforge_are_registered_lazily(self) -> None:
        assert sorted(BackendRegistry().available_backends()) == ["thread", "toolforge"]

    def test_thread_backend_resolves_without_extra_setup(self) -> None:
        assert isinstance(BackendRegistry().get_backend("thread"), ThreadBackend)

    def test_toolforge_backend_class_is_the_default_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Instantiating the real backend needs the Toolforge client; only check the registration here.
        registry = BackendRegistry()
        registry.available_backends()

        assert registry._backends["toolforge"] is ToolforgeBackend
