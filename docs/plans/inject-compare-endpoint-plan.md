# Inject & Compare Endpoint Plan

## Overview

New `/inject` endpoint that takes a **source file** (to extract translations from) and a **target file** (to inject into), performs injection, then re-extracts from the modified target to show a before/after diff.

## Workflow

```
Source file ──extract──> source_translations
                             │
Target file ──extract──> target_translations_before
                             │
                     inject source_translations into target file
                             │
                     new target file written to temp dir
                             │
                     new target ──extract──> target_translations_after
                             │
                     diff(target_translations_before, target_translations_after)
```

## Files to Create

### 1. `src/main_app/public/main_routes/inject_routes.py`

Module-level helper + `InjectRoutes` class (same pattern as `extract_routes.py`).

**Helper functions:**

```python
def extract_from_file(filename: str, temp_dir: Path) -> dict[str, Any]:
    """Download and extract translations from a file. Returns translations dict."""
    # Reuses: download_one_file, CopySVGTranslation.extract
    # Same logic as extract_routes.work_file but takes temp_dir param
    # Returns: translations dict with "new", "title_new", etc.

def inject_translations(
    source_file: Path,
    target_file: Path,
    translations: dict,
    output_dir: Path,
) -> InjectResult:
    """Inject translations into target file. Returns InjectResult."""
    # Uses inject_step_one_file from copy_svg_langs/steps/inject_one_file.py
    # output_file = output_dir / target_file.name
```

**Route class:**

```python
class InjectRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self):
        self.bp.route("/", methods=["GET"])(self.dashboard)      # form
        self.bp.route("/", methods=["POST"])(self.inject_post)   # PRG redirect
        self.bp.route("/<string:source>/<string:target>", methods=["GET"])(self.inject_get)  # result
```

**`inject_post`** — validates both filenames, redirects to `inject_get`.

**`inject_get`** — main workflow:

1. Create temp dir
2. Download source file → extract → `source_translations`
3. Download target file → extract → `target_before`
4. Copy target to output path in temp dir
5. Call `inject_step_one_file(target_file, source_translations, output_file, overwrite=True)`
6. If inject succeeded (result=True): extract from `output_file` → `target_after`
7. Compute diff between `target_before` and `target_after`
8. Render `inject/result.html` with all data
9. Cleanup temp dir in `finally`

**Diff logic:**

```python
def compute_diff(before: dict, after: dict) -> dict:
    """Compare two translations dicts, return added/removed/changed entries."""
    before_new = before.get("new", {})
    after_new = after.get("new", {})
    # new keys = after_new.keys() - before_new.keys()
    # removed keys = before_new.keys() - after_new.keys()
    # existing keys where values differ
```

**Template variables for result:**

-   `source_filename` — display name of source file
-   `target_filename` — display name of target file
-   `source_translations` — extracted from source
-   `target_before` — extracted from target before inject
-   `inject_result` — `InjectResult` (result, msg, new_languages, updated_translations)
-   `target_after` — extracted from target after inject (only if inject succeeded)
-   `diff` — added/removed/changed translations
-   `target_changed` — bool, whether the file was actually modified

### 2. `src/templates/inject/form.html`

Two-field form (source + target), similar structure to `extract/form.html`.

```html
{% extends "base.html" %} {% block title %}Inject SVG Translations{% endblock %}
{% block content_fluid %}
<!-- Card with form -->
<!-- Two inputs: source_filename, target_filename -->
<!-- Both use wiki-autocomplete-files class -->
<!-- POST to url_for('inject.inject_post') -->
<!-- CSRF token hidden field -->
{% endblock %}
```

### 3. `src/templates/inject/result.html`

Shows before/after comparison. Structure:

```
┌─────────────────────────────────────────────┐
│ Inject SVG Translations                     │
├─────────────────────────────────────────────┤
│ Source: File:source.svg  [extracted data]   │
│ Target: File:target.svg                     │
├─────────────────────────────────────────────┤
│ Inject Result: ✅ 3 languages injected      │
├─────────────────────────────────────────────┤
│ Diff                                        │
│   + added: { "en": "...", "ar": "...", ... }│
│   ~ changed: ...                            │
│   - removed: ...                            │
├─────────────────────────────────────────────┤
│ [Full source translations]                  │
│ [Full target-after translations]            │
└─────────────────────────────────────────────┘
```

Reuses existing macros: `card_header`, `commons_file_link`, `render_extract_details`, `render_json`.

## Files to Modify

### 4. `src/main_app/public/main_routes/__init__.py`

Add import:

```python
from .inject_routes import InjectRoutes
```

Add to `__all__`.

### 5. `src/main_app/public/__init__.py`

Add import:

```python
from .main_routes import InjectRoutes
```

Add to `PUBLIC_ROUTE_MODULES`:

```python
PublicRouteModule(InjectRoutes, "inject", "/inject"),
```

## Key Imports

```python
from CopySVGTranslation import extract
from src.main_app.shared.copysvg_wrapper.inject_one_file import (
    inject_step_one_file,
    InjectResult,
)
from ..api_services.files_service import download_one_file, get_file_info
```

## Edge Cases

-   Source or target file doesn't exist → flash error, return form
-   Inject makes no changes (result=None) → still show result, note "no changes"
-   Inject fails (result=False, e.g. nested tspan error) → show error, skip re-extract
-   Source and target are the same file → allow (valid use case for adding translations)
-   Both files have same translations → inject result shows "No changes"

## Testing Strategy

-   Unit test `extract_from_file` mock: download returns temp file, extract returns translations
-   Unit test `inject_translations` mock: calls `inject_step_one_file`
-   Unit test `compute_diff` with known before/after dicts
-   Integration test: full workflow with mocked network (no real Commons calls)
-   Edge cases: file not found, inject failure, no changes
