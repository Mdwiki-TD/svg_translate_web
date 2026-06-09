---
name: patch-to-fixture
description: >
    Refactor pytest test boilerplate into reusable fixtures. Covers two patterns:
    (1) repeated @patch decorators → pytest.fixture with monkeypatch.setattr,
    (2) repeated in-body mock setup blocks (e.g. MagicMock objects built the same way in every test) → parametrized or factory fixtures.
    Use this skill whenever the user wants to clean up pytest tests, reduce repeated mock setup, mentions "pytest fixture",
    "monkeypatch", "patch decorator", or points out boilerplate in test files. Trigger even if only 2 occurrences exist.
---

# Skill: Reduce pytest Boilerplate with Fixtures

## Goal

Two distinct patterns both warrant extraction into fixtures:

1. **Repeated `@patch` decorators** — replace with a fixture using `monkeypatch.setattr`
2. **Repeated in-body mock setup** — replace with a fixture (optionally parametrized or factory-based)

---

## Pattern 1: Repeated `@patch` Decorators

### Steps

#### 1. Analyze the File

Find `@patch("some.module.path")` applied to multiple test functions where **the same path appears ≥ 2 times**.

#### 2. Write the Fixture

```python
@pytest.fixture
def <descriptive_name>(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(
        "full.module.path.to_function",
        _mock,
    )
    return _mock
```

**Naming:** last segment of the path, prefixed with `mock_`.
Example: `src.app.utils.download_core` → `mock_download_core`

#### 3. Update Test Methods

Remove the `@patch(...)` decorator and its corresponding positional argument (right after `self`). Keep the body unchanged.

#### 4. Update Imports

Add `import pytest` and `from unittest.mock import MagicMock`. Remove `from unittest.mock import patch` if no longer used.

### Subvariant: Patching a Class (with instance)

When tests do `mock_class.return_value = MagicMock()` inside the body, the patch target is a **class**. Pre-wire the instance in the fixture:

```python
@pytest.fixture
def mock_worker_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr("src.module.WorkerClass", _mock_class)
    return _mock_class
```

Tests access the instance via `mock_worker_class.return_value` — no per-test setup needed.

### Notes

-   **Stacked `@patch`:** injection order is **reversed** (bottom decorator → first param after `self`).
-   **Single-use patches:** convert or leave based on user preference.
-   **Placement:** module level (after imports) or `conftest.py` for cross-file sharing.
-   **Never touch** unrelated fixtures like `temp_output_dir`, `tmp_path`, etc.

---

## Pattern 2: Repeated In-Body Mock Setup

### When to apply

Look for **3+ lines of identical mock construction** copied across test methods, e.g.:

```python
mock_site = MagicMock(spec=SomeClass)
mock_page = MagicMock()
mock_page.exists = True          # ← this line varies per test
mock_site.pages = MagicMock()
mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
```

Signal: the block is copy-pasted with only **one or two values changing** (e.g. `exists=True` vs `exists=False`).

### Solution A — Factory fixture (preferred when one value varies)

Return a callable that accepts the varying value:

```python
@pytest.fixture
def make_mock_site():
    def _factory(page_exists: bool) -> MagicMock:
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = page_exists
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        return mock_site
    return _factory
```

Tests call it like a function:

```python
def test_something(self, make_mock_site):
    mock_site = make_mock_site(page_exists=True)
    ...
```

### Solution B — Fixed fixture (when all tests use the same setup)

If every test uses the exact same construction with no variation, return the object directly:

```python
@pytest.fixture
def mock_site() -> MagicMock:
    site = MagicMock(spec=mwclient.Site)
    page = MagicMock()
    page.exists = True
    site.pages = MagicMock()
    site.pages.__getitem__ = MagicMock(return_value=page)
    return site
```

### Choosing between A and B

| Situation                                                                                        | Use             |
| ------------------------------------------------------------------------------------------------ | --------------- |
| The varying value is meaningful to the test (e.g. `exists=True` vs `False` drives the assertion) | **Factory (A)** |
| All tests use the same default and override only what they need                                  | **Fixed (B)**   |
| No variation at all                                                                              | **Fixed (B)**   |

### Notes

-   The factory fixture name uses `make_` prefix: `make_mock_site`, `make_mock_page`, etc.
-   Keep the factory signature explicit with typed parameters (`page_exists: bool`).
-   Tests that set additional attributes after calling the factory (e.g. `mock_site.extra = ...`) are fine — the factory gives a starting point.

---

## Complete Examples

### Example 1 — Patching a function (`@patch` → fixture)

**Original:**

```python
from unittest.mock import patch

class TestDownloadCommonsSvgs:
    @patch("src.main_app.api_services.utils.download_file_utils.download_commons_file_core")
    def test_download_single_file(self, mock_download_core, temp_output_dir):
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_commons_svgs(["Example.svg"], temp_output_dir)
        assert len(result) == 1

    @patch("src.main_app.api_services.utils.download_file_utils.download_commons_file_core")
    def test_download_handles_network_error(self, mock_download_core, temp_output_dir):
        import requests
        mock_download_core.side_effect = requests.exceptions.RequestException("Network error")
        result = download_commons_svgs(["NetworkError.svg"], temp_output_dir)
        assert len(result) == 0
```

**Result:**

```python
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_download_core(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.api_services.utils.download_file_utils.download_commons_file_core",
        _mock,
    )
    return _mock


class TestDownloadCommonsSvgs:
    def test_download_single_file(self, mock_download_core, temp_output_dir):
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_commons_svgs(["Example.svg"], temp_output_dir)
        assert len(result) == 1

    def test_download_handles_network_error(self, mock_download_core, temp_output_dir):
        import requests
        mock_download_core.side_effect = requests.exceptions.RequestException("Network error")
        result = download_commons_svgs(["NetworkError.svg"], temp_output_dir)
        assert len(result) == 0
```

---

### Example 2 — Patching a class (with instance)

**Original:**

```python
class TestAddSvgLanguages:
    @patch("src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker.AddSvgSVGLanguagesTemplate")
    def test_function_args_defaults_to_none(self, mock_worker_class, mock_jobs_service):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        add_svglanguages_template_to_templates(job_id=2, user=None)

        mock_worker_class.assert_called_once_with(job_id=2, user=None, cancel_event=None, args=None)
        mock_worker_instance.run.assert_called_once()

    @patch("src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker.AddSvgSVGLanguagesTemplate")
    def test_function_maps_limit_items(self, mock_worker_class, mock_jobs_service):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        add_svglanguages_template_to_templates(job_id=1, user=None, args={"add_svglanguages_limit_items": 10})

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"]["limit_items"] == 10
```

**Result:**

```python
@pytest.fixture
def mock_worker_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker.AddSvgSVGLanguagesTemplate",
        _mock_class,
    )
    return _mock_class


class TestAddSvgLanguages:
    def test_function_args_defaults_to_none(self, mock_worker_class, mock_jobs_service):
        mock_worker_instance = mock_worker_class.return_value  # already wired in fixture

        add_svglanguages_template_to_templates(job_id=2, user=None)

        mock_worker_class.assert_called_once_with(job_id=2, user=None, cancel_event=None, args=None)
        mock_worker_instance.run.assert_called_once()

    def test_function_maps_limit_items(self, mock_worker_class, mock_jobs_service):
        add_svglanguages_template_to_templates(job_id=1, user=None, args={"add_svglanguages_limit_items": 10})

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"]["limit_items"] == 10
```

---

### Example 3 — Repeated in-body setup (factory fixture)

**Original:**

```python
class TestIsPageExists:
    def test_page_exists_returns_true(self) -> None:
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = True
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)

        result = is_page_exists("File:Test.svg", mock_site)

        assert result is True

    def test_page_not_exists_returns_false(self) -> None:
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = False
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)

        result = is_page_exists("File:NonExistent.svg", mock_site)

        assert result is False


class TestCreatePage:
    def test_create_page_success(self) -> None:
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = False
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)

        result = create_page(page_name="File:Test.svg", wikitext="{{Information}}", site=mock_site, summary="Test")

        assert result == {"success": True}
```

**Result:**

```python
import pytest
from unittest.mock import MagicMock
import mwclient


@pytest.fixture
def make_mock_site():
    def _factory(page_exists: bool) -> MagicMock:
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = page_exists
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        return mock_site
    return _factory


class TestIsPageExists:
    def test_page_exists_returns_true(self, make_mock_site) -> None:
        mock_site = make_mock_site(page_exists=True)

        result = is_page_exists("File:Test.svg", mock_site)

        assert result is True

    def test_page_not_exists_returns_false(self, make_mock_site) -> None:
        mock_site = make_mock_site(page_exists=False)

        result = is_page_exists("File:NonExistent.svg", mock_site)

        assert result is False


class TestCreatePage:
    def test_create_page_success(self, make_mock_site) -> None:
        mock_site = make_mock_site(page_exists=False)

        result = create_page(page_name="File:Test.svg", wikitext="{{Information}}", site=mock_site, summary="Test")

        assert result == {"success": True}
```

Key changes:

-   5-line setup block removed from every test
-   `page_exists` is now explicit in the call — makes test intent immediately clear
-   The fixture is shared across `TestIsPageExists` **and** `TestCreatePage` since both needed the same object
