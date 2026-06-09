---
name: patch-to-fixture
description: >
    Refactor repeated @patch decorators in pytest files into reusable pytest.fixture using monkeypatch.setattr.
    Use this skill whenever the user wants to clean up or refactor pytest tests that repeat the same @patch path
    across multiple test methods, or when they mention "pytest fixture", "monkeypatch", "patch decorator",
    or ask to reduce boilerplate in test files. Trigger even if only 2 occurrences of the same patch path exist.
---

# Skill: Convert @patch to pytest.fixture

## Goal

Identify repeated `@patch(...)` decorators in pytest files and replace them with a `pytest.fixture` that uses `monkeypatch.setattr`.

---

## Steps

### 1. Analyze the File

Read the test file and find:

-   `@patch("some.module.path")` decorators applied to multiple test functions
-   The same patch path appearing **2 or more times** across the file

### 2. Identify Candidates

For each patch path, count occurrences. Any path appearing **≥ 2 times** is a candidate for extraction into a fixture.

### 3. Write the Fixture

For each candidate path, create a fixture using this exact shape:

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

**Naming rules:**

-   Use the last segment of the path, prefixed with `mock_`
-   Example: `src.app.utils.download_core` → `mock_download_core`
-   If ambiguous, choose a short descriptive name that reflects purpose

### 4. Update Test Methods

For every test that had `@patch`:

**Before:**

```python
@patch("src.module.some_function")
def test_example(self, mock_some_function, other_fixture):
    mock_some_function.return_value = "value"
    ...
```

**After:**

```python
def test_example(self, mock_some_function, other_fixture):
    mock_some_function.return_value = "value"
    ...
```

Changes to make:

1. Remove the `@patch(...)` decorator line
2. Remove the corresponding positional argument from the method signature (usually right after `self`)
3. Keep all body code unchanged — the variable name stays the same

### 5. Update Imports

Ensure these imports are present at the top of the file:

```python
import pytest
from unittest.mock import MagicMock
```

If `from unittest.mock import patch` is no longer used anywhere, remove it.

---

## Important Notes

-   **Multiple `@patch` on one method:** When stacked decorators exist on a single test, parameters are injected in **reverse order** (bottom decorator → first param after `self`). Identify carefully which argument maps to which patch path before removing.
-   **Single-use patches:** If a path appears only once in the whole file, you may leave it as `@patch` or convert it — follow the user's preference.
-   **Fixture placement:** Place new fixtures at module level (after imports, before any class), or in `conftest.py` if the user wants them shared across multiple test files.
-   **Leave existing fixtures alone:** Do not modify unrelated fixtures like `temp_output_dir`, `tmp_path`, etc.

---

## Complete Example

### Original:

```python
from unittest.mock import patch

class TestDownloadCommonsSvgs:
    @patch("src.main_app.api_services.utils.download_file_utils.download_commons_file_core")
    def test_download_single_file(self, mock_download_core, temp_output_dir):
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_commons_svgs(["Example.svg"], temp_output_dir)
        assert len(result) == 1

    @patch("src.main_app.api_services.utils.download_file_utils.download_commons_file_core")
    def test_download_multiple_files(self, mock_download_core, temp_output_dir):
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_commons_svgs(["File1.svg", "File2.svg"], temp_output_dir)
        assert len(result) == 2

    @patch("src.main_app.api_services.utils.download_file_utils.download_commons_file_core")
    def test_download_handles_network_error(self, mock_download_core, temp_output_dir):
        import requests
        mock_download_core.side_effect = requests.exceptions.RequestException("Network error")
        result = download_commons_svgs(["NetworkError.svg"], temp_output_dir)
        assert len(result) == 0
```

### Result:

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

    def test_download_multiple_files(self, mock_download_core, temp_output_dir):
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_commons_svgs(["File1.svg", "File2.svg"], temp_output_dir)
        assert len(result) == 2

    def test_download_handles_network_error(self, mock_download_core, temp_output_dir):
        import requests
        mock_download_core.side_effect = requests.exceptions.RequestException("Network error")
        result = download_commons_svgs(["NetworkError.svg"], temp_output_dir)
        assert len(result) == 0
```
