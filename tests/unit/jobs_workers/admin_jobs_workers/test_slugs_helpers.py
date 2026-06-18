# ruff: noqa: F401
"""
Unit tests for src/main_app/jobs_workers/admin_jobs_workers/slugs_helpers.py module.

Functions to test: check_slugs
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.slugs_helpers import check_slugs


class TestCheckSlugs:
    """Tests for check_slugs function."""

    @pytest.fixture(autouse=True)
    def _setup_mocks(self) -> None:
        """Patch extract_slug and add_new_slug_redirect for every test."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.slugs_helpers.extract_slug",
        ) as mock_extract:
            with patch(
                "src.main_app.jobs_workers.admin_jobs_workers.slugs_helpers.add_new_slug_redirect",
            ) as mock_add:
                self.mock_extract_slug = mock_extract
                self.mock_add_new_slug_redirect = mock_add
                yield

    def test_missing_chart_key_returns_false(self) -> None:
        """Returns False when metadata has no 'chart' key."""
        metadata: dict = {}

        result = check_slugs("some-slug", metadata)

        assert result is False
        self.mock_extract_slug.assert_not_called()
        self.mock_add_new_slug_redirect.assert_not_called()

    def test_missing_original_chart_url_returns_false(self) -> None:
        """Returns False when 'chart' key has no 'originalChartUrl'."""
        metadata: dict = {"chart": {}}

        result = check_slugs("some-slug", metadata)

        assert result is False
        self.mock_extract_slug.assert_not_called()
        self.mock_add_new_slug_redirect.assert_not_called()

    def test_empty_original_chart_url_returns_false(self) -> None:
        """Returns False when originalChartUrl is an empty string."""
        metadata: dict = {"chart": {"originalChartUrl": ""}}

        result = check_slugs("some-slug", metadata)

        assert result is False
        self.mock_extract_slug.assert_not_called()
        self.mock_add_new_slug_redirect.assert_not_called()

    def test_extract_slug_returns_none_returns_false(self) -> None:
        """Returns False when extract_slug returns None."""
        self.mock_extract_slug.return_value = None
        metadata: dict = {"chart": {"originalChartUrl": "https://example.com/chart"}}

        result = check_slugs("some-slug", metadata)

        assert result is False
        self.mock_extract_slug.assert_called_once_with("https://example.com/chart")
        self.mock_add_new_slug_redirect.assert_not_called()

    def test_extract_slug_returns_empty_string_returns_false(self) -> None:
        """Returns False when extract_slug returns an empty string."""
        self.mock_extract_slug.return_value = ""
        metadata: dict = {"chart": {"originalChartUrl": "https://example.com/chart"}}

        result = check_slugs("some-slug", metadata)

        assert result is False
        self.mock_extract_slug.assert_called_once_with("https://example.com/chart")
        self.mock_add_new_slug_redirect.assert_not_called()

    def test_original_slug_equals_slug_to_check_returns_false(self) -> None:
        """Returns False when the extracted slug matches slug_to_check."""
        self.mock_extract_slug.return_value = "same-slug"
        metadata: dict = {"chart": {"originalChartUrl": "https://example.com/chart"}}

        result = check_slugs("same-slug", metadata)

        assert result is False
        self.mock_extract_slug.assert_called_once()
        self.mock_add_new_slug_redirect.assert_not_called()

    def test_add_new_slug_redirect_succeeds_returns_true(self) -> None:
        """Returns True when add_new_slug_redirect completes successfully."""
        self.mock_extract_slug.return_value = "original-slug"
        self.mock_add_new_slug_redirect.return_value = None
        metadata: dict = {"chart": {"originalChartUrl": "https://example.com/chart"}}

        result = check_slugs("new-slug", metadata)

        assert result is True
        self.mock_extract_slug.assert_called_once_with("https://example.com/chart")
        self.mock_add_new_slug_redirect.assert_called_once_with(
            slug="new-slug",
            redirect_to="original-slug",
        )

    def test_add_new_slug_redirect_raises_exception_logs_and_returns_false(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Returns False and logs an error when add_new_slug_redirect raises."""
        self.mock_extract_slug.return_value = "original-slug"
        self.mock_add_new_slug_redirect.side_effect = RuntimeError("DB error")
        metadata: dict = {"chart": {"originalChartUrl": "https://example.com/chart"}}

        result = check_slugs("new-slug", metadata)

        assert result is False
        self.mock_extract_slug.assert_called_once_with("https://example.com/chart")
        self.mock_add_new_slug_redirect.assert_called_once_with(
            slug="new-slug",
            redirect_to="original-slug",
        )
        assert "Error adding slug redirect: DB error" in caplog.text
