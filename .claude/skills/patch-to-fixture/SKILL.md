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

Three distinct patterns warrant extraction into fixtures:

1. **Repeated `@patch` decorators** — replace with a fixture using `monkeypatch.setattr`
2. **Repeated in-body mock setup** — replace with a fixture (optionally parametrized or factory-based)
3. **Grouped Service Mocks (Bundle)** — replace multiple related mocks with a single "service bundle" fixture.

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

## Pattern 3: Many Fixtures → One `dataclass` Fixture

### When to apply

Two sub-cases, same solution:

**Sub-case A — Many individual fixtures with identical structure:**
When the file defines 5+ separate fixtures that all follow the same `monkeypatch.setattr` shape:

```python
@pytest.fixture
def mock_save_job_result(monkeypatch): ...

@pytest.fixture
def mock_is_job_cancelled(monkeypatch): ...

@pytest.fixture
def mock_download_svg_file(monkeypatch): ...

@pytest.fixture
def mock_detect_nested_tags(monkeypatch): ...
# ... and so on
```

Each test then lists all of them as parameters: `def test_x(self, mock_save_job_result, mock_is_job_cancelled, mock_download_svg_file, ...)` — long, repetitive signatures.

**Sub-case B — One fixture returning a `dict` of mocks:**

```python
return {
    "create_page": mock_create_page,
    "update_page_text": mock_update_page_text,
    ...  # 5+ keys
}
```

Accessing via `mock_services["create_page"]` has no autocomplete and is prone to silent key typos.

**The fix for both:** merge everything into **one fixture** that returns a typed `@dataclass`.

### How to apply

#### 1. Define a dataclass next to the fixture

```python
from dataclasses import dataclass

@dataclass
class MockServices:
    create_page: MagicMock
    update_page_text: MagicMock
    list_templates: MagicMock
    get_user_site: MagicMock
    # ... one field per mock
```

**Naming convention:** `Mock<WorkerOrContextName>` (e.g. `MockServices`, `MockWorkerDeps`, `MockSiteServices`)

#### 2. Change the fixture return type and return statement

```python
@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch) -> MockServices:
    # ... all monkeypatch.setattr calls unchanged ...

    return MockServices(
        create_page=mock_create_page,
        update_page_text=mock_update_page_text,
        list_templates=mock_list_templates,
        get_user_site=mock_get_user_site,
        # ...
    )
```

#### 3. Update tests to use attribute access

```python
# Before
def test_something(self, mock_services):
    mock_services["create_page"].assert_called_once()

# After
def test_something(self, mock_services: MockServices):
    mock_services.create_page.assert_called_once()
```

### Threshold: when to apply

| Number of mocks in the dict | Recommendation                  |
| --------------------------- | ------------------------------- |
| ≤ 4                         | Dict is fine, skip this pattern |
| 5–7                         | Consider dataclass              |
| 8+                          | Always use dataclass            |

### Notes

-   Place the `@dataclass` class **just above** the fixture that uses it, not at the top of the file.
-   Add the type annotation to every test parameter that receives this fixture: `mock_services: MockServices` — this is what enables IDE autocomplete.
-   `dataclass` is preferred over `NamedTuple` here because fields may need to be reassigned in tests (`mock_services.create_page.return_value = ...` already works; no mutation of the dataclass itself is needed).
-   Do **not** add `frozen=True` — tests may do `mock_services.some_mock.return_value = x` which mutates the mock, not the dataclass.

---

## Complete Examples

### Example 1 — Patching a function (`@patch` → fixture)

**Original:**

```python
from unittest.mock import patch

class TestDownloadCommonsSvgs:
    @patch("src.main_app.api_services.utils.download_file_utils.download_file_rate_limit")
    def test_download_single_file(self, mock_download_core, temp_output_dir):
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_commons_svgs(["Example.svg"], temp_output_dir)
        assert len(result) == 1

    @patch("src.main_app.api_services.utils.download_file_utils.download_file_rate_limit")
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
        "src.main_app.api_services.utils.download_file_utils.download_file_rate_limit",
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
    def test_function_args_defaults_to_none(self, mock_worker_class):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        add_svglanguages_template_to_templates(job_id=2, user=None)

        mock_worker_class.assert_called_once_with(job_id=2, user=None, cancel_event=None, args=None)
        mock_worker_instance.run.assert_called_once()

    @patch("src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker.AddSvgSVGLanguagesTemplate")
    def test_function_maps_limit_items(self, mock_worker_class):
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
    def test_function_args_defaults_to_none(self, mock_worker_class):
        mock_worker_instance = mock_worker_class.return_value  # already wired in fixture

        add_svglanguages_template_to_templates(job_id=2, user=None)

        mock_worker_class.assert_called_once_with(job_id=2, user=None, cancel_event=None, args=None)
        mock_worker_instance.run.assert_called_once()

    def test_function_maps_limit_items(self, mock_worker_class):
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

---

### Example 4 — Large fixture dict → dataclass

**Original:**

```python
@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    mock_create_page = MagicMock()
    monkeypatch.setattr("...worker.create_page", mock_create_page)

    mock_update_page_text = MagicMock()
    monkeypatch.setattr("...worker.update_page_text", mock_update_page_text)

    mock_list_templates = MagicMock()
    monkeypatch.setattr("...worker.list_templates", mock_list_templates)

    mock_get_user_site = MagicMock()
    monkeypatch.setattr("...worker.get_user_site", mock_get_user_site)

    mock_is_pages_exists = MagicMock(return_value={})
    monkeypatch.setattr("...worker.is_pages_exists", mock_is_pages_exists)

    return {
        "create_page": mock_create_page,
        "update_page_text": mock_update_page_text,
        "list_templates": mock_list_templates,
        "get_user_site": mock_get_user_site,
        "is_pages_exists": mock_is_pages_exists,
    }


class TestCreateOwidPages:
    def test_creates_new_page(self, mock_services):
        mock_services["list_templates"].return_value = [...]
        mock_services["is_pages_exists"].return_value = {}
        ...
        mock_services["create_page"].assert_called_once()
```

**Result:**

```python
from dataclasses import dataclass


@dataclass
class MockServices:
    create_page: MagicMock
    update_page_text: MagicMock
    list_templates: MagicMock
    get_user_site: MagicMock
    is_pages_exists: MagicMock


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch) -> MockServices:
    mock_create_page = MagicMock()
    monkeypatch.setattr("...worker.create_page", mock_create_page)

    mock_update_page_text = MagicMock()
    monkeypatch.setattr("...worker.update_page_text", mock_update_page_text)

    mock_list_templates = MagicMock()
    monkeypatch.setattr("...worker.list_templates", mock_list_templates)

    mock_get_user_site = MagicMock()
    monkeypatch.setattr("...worker.get_user_site", mock_get_user_site)

    mock_is_pages_exists = MagicMock(return_value={})
    monkeypatch.setattr("...worker.is_pages_exists", mock_is_pages_exists)

    return MockServices(
        create_page=mock_create_page,
        update_page_text=mock_update_page_text,
        list_templates=mock_list_templates,
        get_user_site=mock_get_user_site,
        is_pages_exists=mock_is_pages_exists,
    )


class TestCreateOwidPages:
    def test_creates_new_page(self, mock_services: MockServices):
        mock_services.list_templates.return_value = [...]
        mock_services.is_pages_exists.return_value = {}
        ...
        mock_services.create_page.assert_called_once()
```

Key changes:

-   `dict` access `mock_services["key"]` → attribute access `mock_services.key`
-   Type annotation on test parameter enables IDE autocomplete
-   `@dataclass` defined just above the fixture

---

### Example 5 — Many individual fixtures → one dataclass fixture (Sub-case A)

**Original:**

```python
@pytest.fixture
def mock_save_job_result(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker.save_job_result_by_name", _mock)
    return _mock

@pytest.fixture
def mock_is_job_cancelled(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker.is_job_cancelled", _mock)
    return _mock

@pytest.fixture
def mock_download_svg_file(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.download_svg_file", _mock)
    return _mock

@pytest.fixture
def mock_detect_nested_tags(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.detect_nested_tags", _mock)
    return _mock

@pytest.fixture
def mock_fix_nested_tags(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.fix_nested_tags", _mock)
    return _mock

@pytest.fixture
def mock_verify_fix(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.verify_fix", _mock)
    return _mock

@pytest.fixture
def mock_upload_fixed_svg(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.upload_fixed_svg", _mock)
    return _mock


class TestFixNestedJobs:
    def test_something(
        self,
        mock_save_job_result,
        mock_is_job_cancelled,
        mock_download_svg_file,
        mock_detect_nested_tags,
        mock_fix_nested_tags,
        mock_verify_fix,
        mock_upload_fixed_svg,
    ):
        mock_download_svg_file.return_value = b"<svg/>"
        mock_detect_nested_tags.return_value = True
        ...
        mock_upload_fixed_svg.assert_called_once()
```

**Result:**

```python
from dataclasses import dataclass


@dataclass
class MockFixNestedJobsDeps:
    save_job_result: MagicMock
    is_job_cancelled: MagicMock
    download_svg_file: MagicMock
    detect_nested_tags: MagicMock
    fix_nested_tags: MagicMock
    verify_fix: MagicMock
    upload_fixed_svg: MagicMock


@pytest.fixture
def mock_deps(monkeypatch: pytest.MonkeyPatch) -> MockFixNestedJobsDeps:
    _base = "src.main_app.jobs_workers.base_worker"
    _worker = "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker"

    mock_save_job_result = MagicMock()
    monkeypatch.setattr(f"{_base}.save_job_result_by_name", mock_save_job_result)

    mock_is_job_cancelled = MagicMock()
    monkeypatch.setattr(f"{_base}.is_job_cancelled", mock_is_job_cancelled)

    mock_download_svg_file = MagicMock()
    monkeypatch.setattr(f"{_worker}.download_svg_file", mock_download_svg_file)

    mock_detect_nested_tags = MagicMock()
    monkeypatch.setattr(f"{_worker}.detect_nested_tags", mock_detect_nested_tags)

    mock_fix_nested_tags = MagicMock()
    monkeypatch.setattr(f"{_worker}.fix_nested_tags", mock_fix_nested_tags)

    mock_verify_fix = MagicMock()
    monkeypatch.setattr(f"{_worker}.verify_fix", mock_verify_fix)

    mock_upload_fixed_svg = MagicMock()
    monkeypatch.setattr(f"{_worker}.upload_fixed_svg", mock_upload_fixed_svg)

    return MockFixNestedJobsDeps(
        save_job_result=mock_save_job_result,
        is_job_cancelled=mock_is_job_cancelled,
        download_svg_file=mock_download_svg_file,
        detect_nested_tags=mock_detect_nested_tags,
        fix_nested_tags=mock_fix_nested_tags,
        verify_fix=mock_verify_fix,
        upload_fixed_svg=mock_upload_fixed_svg,
    )


class TestFixNestedJobs:
    def test_something(self, mock_deps: MockFixNestedJobsDeps):
        mock_deps.download_svg_file.return_value = b"<svg/>"
        mock_deps.detect_nested_tags.return_value = True
        ...
        mock_deps.upload_fixed_svg.assert_called_once()
```

Key changes:

-   7 separate fixtures → 1 fixture with 1 dataclass
-   Test signature: 7 parameters → 1 parameter (`mock_deps: MockFixNestedJobsDeps`)
-   Path prefixes extracted into local variables (`_base`, `_worker`) to reduce repetition
-   Full IDE autocomplete on `mock_deps.<TAB>`
