# Plan: Add Language Categories to OWID Pages (Background Job)

## Goal

Create a new admin background job `add_lang_categories_to_owid_pages` that iterates all `OWID/*` pages (main namespace), determines which languages the underlying SVG supports, and appends `[[Category:<Lang>-language SVG]]` entries to each page.

### Target Example

For `OWID/Coverage_of_the_human_papillomavirus_vaccine`, if the SVG has translations in Japanese, English, and Arabic, the job appends:

```wikitext
[[Category:Japanese-language SVG]]
[[Category:English-language SVG]]
[[Category:Arabic-language SVG]]
```

---

## Files to Create (7 new files)

All under `src/main_app/jobs_workers/admin_jobs_workers/add_lang_categories_to_owid_pages/`:

| #   | File          | Purpose                                                                         |
| --- | ------------- | ------------------------------------------------------------------------------- |
| 1   | `__init__.py` | Exports `add_lang_categories_to_owid_pages_entry`                               |
| 2   | `runner.py`   | Entry-point function matching the `job_callable` signature                      |
| 3   | `worker.py`   | `AddLangCategoriesWorker` extending `BaseObjectsJobWorker`                      |
| 4   | `objects.py`  | `AddLangCategoriesWorkerObject` + summary dataclass                             |
| 5   | `utils.py`    | Helper: extract SVG file name, build category lines, detect existing categories |

Plus 2 template files:

| #   | File                                                                                          | Purpose                                                 |
| --- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 6   | `src/templates/jobs_templates/admin_templates/add_lang_categories_to_owid_pages/list.html`    | Extends `base_list.html` with job description           |
| 7   | `src/templates/jobs_templates/admin_templates/add_lang_categories_to_owid_pages/details.html` | Extends `base_details.html` with per-page results table |

## Files to Modify (2 existing files)

| #   | File                                                           | Change                                                                    |
| --- | -------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 8   | `src/main_app/jobs_workers/admin_jobs_workers/workers_list.py` | Register `"add_lang_categories_to_owid_pages"` in `jobs_data_admins` dict |
| 9   | `src/main_app/admin/sidebar.py`                                | Add a `SidebarItem` under the **"OWID Templates/Pages"** group            |

## File to Potentially Expand

| #   | File                                                        | Change                                                                                                                                                                                          |
| --- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 10  | `src/main_app/utils/file_langs.py` — `lang_code_category()` | Currently only maps `"ar"` and `"en"`. Needs a comprehensive mapping of Wikimedia language codes → display names (e.g., `"ja" → "Japanese-language SVG"`, `"fr" → "French-language SVG"`, etc.) |

---

## Worker Logic (`worker.py`)

**Class**: `AddLangCategoriesWorker(BaseObjectsJobWorker)`

**`get_job_type()`** → `"add_lang_categories_to_owid_pages"`

### `process()` flow:

1. **`_check_site()`** — ensure authenticated user site is available
2. **Discover pages** — iterate all pages with prefix `OWID/` in namespace `0` (main namespace) using `self.site.allpages(prefix="OWID/", namespace=0, filterredir="nonredirects")`
3. **Apply limit** (if `limit_items` arg is provided)
4. **For each OWID page**, call `_process_one_item(page)`:
    - **Step 1 — `load_page_text`**: Get page wikitext via `MwClientPage.get_text()`
    - **Step 2 — `extract_file_name`**: Use the `RE_TRANSLATE` regex (same pattern from `add_svglanguages_template/utils.py`) to extract the SVG file name from the `*'''Translate''': https://svgtranslate.toolforge.org/File:XXX.svg` line
    - **Step 3 — `get_languages`**: Call `get_file_languages(file_name)` from `src/main_app/utils/file_langs.py` → returns list of lang codes (e.g., `["en", "ja", "ar"]`)
    - **Step 4 — `build_categories`**: For each lang code, call `lang_code_category(code)`. Filter out `None` returns (unknown codes). Build `[[Category:XXX-language SVG]]` strings
    - **Step 5 — `check_existing`**: Parse current page text to find which `*-language SVG` categories already exist. Subtract them from the new set
    - **Step 6 — `save_page`**: If new categories remain, append them to the page text and call `MwClientPage.edit()` with summary `"Adding language categories: [[Category:...]]"`
5. **Track per-item results** into `pages_success`, `pages_skipped`, `pages_failed`
6. **Cancellation checks**: `self.is_cancelled()` between items, `self.check_cancel_db_periodic()` after each successful edit
7. **Progress saves**: every `get_priority(total)` items

---

## `utils.py` — Helper Functions

```python
# Key functions:

def extract_svg_file_name(text: str) -> str | None:
    """Extract SVG file name from the Translate link in page wikitext.
    Reuses the RE_TRANSLATE regex pattern."""

def build_category_lines(lang_codes: list[str]) -> list[str]:
    """Convert lang codes to [[Category:XXX-language SVG]] lines.
    Skips codes where lang_code_category() returns None."""

def get_existing_lang_categories(text: str) -> set[str]:
    """Parse page text to find existing [[Category:*-language SVG]] entries.
    Uses regex: r'\[\[Category:[^\]]*-language SVG\]\]'"""

def add_categories_to_text(text: str, new_categories: list[str]) -> str:
    """Append category lines to the end of the page text."""
```

---

## `objects.py` — Result Object

```python
@dataclass
class AddLangCategoriesSummary:
    total: int = 0
    processed: int = 0
    success: int = 0       # pages that got new categories added
    skipped: int = 0       # pages where all categories already exist
    failed: int = 0
    no_file: int = 0       # pages where no SVG file name could be extracted

@dataclass
class AddLangCategoriesWorkerObject(StandardAdminWorkerObject):
    summary: AddLangCategoriesSummary = field(default_factory=AddLangCategoriesSummary)
```

---

## Registration (`workers_list.py`)

Add entry to `jobs_data_admins`:

```python
"add_lang_categories_to_owid_pages": JobData(
    job_type="add_lang_categories_to_owid_pages",
    job_name="Add Language Categories",
    job_details_template="jobs_templates/admin_templates/add_lang_categories_to_owid_pages/details.html",
    job_list_template="jobs_templates/admin_templates/add_lang_categories_to_owid_pages/list.html",
    job_callable=add_lang_categories_to_owid_pages_entry,
    job_args=[
        {"key": "add_lang_categories_limit_items", "as": "limit_items"},
    ],
    start_confirm_message=(
        "This will add language categories (e.g. [[Category:English-language SVG]]) "
        "to OWID pages based on available SVG translations. Continue?"
    ),
),
```

## Sidebar (`sidebar.py`)

Add a new `SidebarItem` in the existing `owid_temp_pages` group, after `add_svglanguages_template`:

```python
SidebarItem(
    id="add_lang_categories_to_owid_pages",
    admin=1,
    href=job_list_url("add_lang_categories_to_owid_pages"),
    title="Add Lang Categories",
    icon="bi-tags",
),
```

---

## ⚠️ Important: `lang_code_category()` Expansion

The current implementation in `src/main_app/utils/file_langs.py` only maps 2 codes:

```python
data = {"ar": "Arabic-language SVG", "en": "English-language SVG"}
```

For this job to be useful, this needs to be expanded to cover all Wikimedia language codes that SVG translations support. This could be a static dict of ~50-100+ common codes, or could be loaded from a config/JSON file. **This is a prerequisite for the job to produce meaningful results.**

---

## Templates (minimal)

-   **`list.html`**: Extends `base_list.html`, adds a description block.
-   **`details.html`**: Extends `base_details.html`, shows summary cards (Processed/Success/Skipped/Failed) and a table with columns: `#`, `OWID Page`, `SVG File`, `Languages Found`, `Categories Added`, `Status`.

---

## Execution Order for Implementation

1. Expand `lang_code_category()` in `file_langs.py`
2. Create the 5 Python files in the new worker directory
3. Create the 2 HTML template files
4. Register in `workers_list.py`
5. Add sidebar item in `sidebar.py`
6. Write tests
