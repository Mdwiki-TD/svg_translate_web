# Plan: Migrate Admin `details.html` Tables to DataTables AJAX

## Overview

Convert all admin job detail templates under:

```
src/templates/jobs_templates/admin_templates/<job_type>/details.html
```

from server-rendered Jinja tables (with `table_header_to_expand` collapse/expand) to
client-side DataTables powered by the existing AJAX infrastructure:

-   `src/static/js/data_table_ajax/table.js` — `initServerTable(tableId, columns)`
-   `src/static/js/data_table_ajax/macros.js` — `renderStatus`, `renderCommonsLink`, `renderStep`, `statusClass`

### Reference examples (already migrated)

-   `src/templates/jobs_templates/public/copy_svg_langs/details.html`
-   `src/templates/jobs_templates/public/extract_files_translations/details.html`

### Target files (9 templates)

| #   | File                                             | Job Type                            |
| --- | ------------------------------------------------ | ----------------------------------- |
| 1   | `add_lang_categories_to_owid_pages/details.html` | `add_lang_categories_to_owid_pages` |
| 2   | `add_svglanguages_template/details.html`         | `add_svglanguages_template`         |
| 3   | `collect_templates_data/details.html`            | `collect_templates_data`            |
| 4   | `create_owid_pages/details.html`                 | `create_owid_pages`                 |
| 5   | `crop_main_files/details.html`                   | `crop_main_files`                   |
| 6   | `download_main_files/details.html`               | `download_main_files`               |
| 7   | `fix_nested_main_files/details.html`             | `fix_nested_main_files`             |
| 8   | `rename_owid_pages/details.html`                 | `rename_owid_pages`                 |
| 9   | `update_owid_charts/details.html`                | `update_owid_charts`                |

---

## Prerequisites (Shared Infrastructure)

### P1. Parameterize `_ajax_table.html` macro to support admin blueprint

**File:** `src/templates/jobs_templates/_ajax_templates/_ajax_table.html`

The current `new_pages_table` macro hardcodes `url_for('public_jobs.draw_result_file', ...)`.
Add an optional `bp_name` parameter (default `'public_jobs'`) so admin templates can pass
`'adminpanel.jobs'`:

```jinja2
{% macro new_pages_table(table_title, job_id, job_type, list_name, table_headers, bp_name='public_jobs') %}
...
  data-ajax-url="{{ url_for(bp_name ~ '.draw_result_file', job_type=job_type, file_number=job_id, list_name=list_name) }}"
...
{% endmacro %}
```

This is backward-compatible — all existing public callers continue to work unchanged.

**Note:** The admin route `draw_result_file` already exists at:

-   `src/main_app/admin/routes/jobs.py` line 42:
    `("/<string:job_type>/file/<int:file_number>/<string:list_name>", "GET", self.draw_result_file)`
-   It inherits the implementation from `src/main_app/public/shared_jobs_routes.py` (class `JobsBp`).

---

## Phase 1 — Simplest: `pages_skipped` (3 columns: `#`, `Title`, `Reason`)

Start here because the data shape is the simplest across all templates that use it.

### Step 1a: `add_svglanguages_template/details.html`

| Current                                                                                       | Replacement                                                                     |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `pages_skipped_table(wiki_domain, result_data.pages_skipped, ...)` from `_skipped_table.html` | `new_pages_table(...)` from `_ajax_table.html` with `bp_name='adminpanel.jobs'` |

**List names to convert:** `pages_skipped`

**JS columns definition:**

```js
function createSkippedColumns() {
    return [
        {
            data: null,
            title: "#",
            render: (data, type, row, meta) => meta.row + 1,
        },
        {
            data: "title",
            title: "Title",
            render: renderCommonsLink,
        },
        {
            data: "reason",
            title: "Reason",
            render: (data) => data || "-",
        },
    ];
}
```

**Steps:**

1. Add `{% from 'jobs_templates/_ajax_templates/_ajax_table.html' import new_pages_table %}`
2. Remove import of `pages_skipped_table` from `_skipped_table.html` (if no longer used)
3. Replace the `pages_skipped_table(...)` call with:
    ```jinja2
    {{ new_pages_table(
        table_title="Skipped Templates",
        job_id=job.id,
        job_type=template_data.job_type,
        list_name="pages_skipped",
        table_headers=["#", "Title", "Reason"],
        bp_name='adminpanel.jobs'
    ) }}
    ```
4. Add `{% block extra_js %}` with:
    ```js
    $(document).ready(function () {
        initServerTable("table-pages_skipped", createSkippedColumns());
    });
    ```
5. The `pages_processed_table` and other macros in this file stay as-is for now (Phase 3)

---

## Phase 2 — Simple Inline Tables (2–4 columns, no step rendering)

### Step 2a: `fix_nested_main_files/details.html`

| List            | Columns                               |
| --------------- | ------------------------------------- |
| `pages_success` | `#`, `Title`, `Oldest File`, `Result` |
| `pages_failed`  | `#`, `Title`, `Oldest File`, `Reason` |
| `pages_skipped` | `#`, `Title`, `Oldest File`, `Reason` |

**Steps:** Replace all 3 inline tables with `new_pages_table(...)`.
The `pages_failed` and `pages_skipped` share the same column shape, so one
`createResultColumns()` function with a `show_result` toggle suffices.

### Step 2b: `download_main_files/details.html`

| List               | Columns                                      |
| ------------------ | -------------------------------------------- |
| `files_downloaded` | `ID`, `Filename`, `View`, `Size`             |
| `files_skipped`    | `ID`, `Template Title`, `Filename`, `Reason` |
| `files_failed`     | `ID`, `Template Title`, `Filename`, `Reason` |

**Special note:** `files_downloaded` has a `View` column with a custom link
(`url_for('jobs_utils.serve_download_main_file', ...)`). This needs a custom render function
that embeds the URL pattern or passes the base URL via a data attribute.

### Step 2c: `collect_templates_data/details.html` — `pages_added` table only

| List          | Columns      |
| ------------- | ------------ |
| `pages_added` | `#`, `Title` |

**Steps:** Replace the inline table with `new_pages_table(...)`. Very simple — just 2 columns.

### Step 2d: `rename_owid_pages/details.html`

| List               | Columns                                                          |
| ------------------ | ---------------------------------------------------------------- |
| `pages_renamed`    | `#`, `Old title`, `New title`, `Message`                         |
| `pages_skipped`    | `#`, `Old title`, `New title`, `Message`                         |
| `pages_redirected` | `#`, `Old title (now redirect)`, `New title (target)`, `Message` |
| `pages_failed`     | `#`, `Old title`, `New title`, `Message`                         |

**Steps:** All 4 lists share the same column shape. One `createColumns()` function.
The `pages_redirected` list currently has an info alert — keep that alert above the table card.

---

## Phase 3 — Medium Complexity (step rendering, 6–7 columns)

### Step 3a: `add_svglanguages_template/details.html` — `pages_processed_table`

| List              | Columns                                                                |
| ----------------- | ---------------------------------------------------------------------- |
| `pages_processed` | `#`, `Template`, `Load Text`, `Generate Text`, `Add text`, `Save Page` |
| `pages_success`   | same                                                                   |
| `pages_failed`    | same                                                                   |

**Steps:** Replace the local `pages_processed_table` macro with `new_pages_table(...)`.
Use `renderStep` from `macros.js` for the 4 step columns.

### Step 3b: `create_owid_pages/details.html`

| List              | Columns                                                                                 |
| ----------------- | --------------------------------------------------------------------------------------- |
| `pages_created`   | `#`, `Template`, `New Page`, `Load Text`, `Generate Text`, `Update Page`, `Create Page` |
| `pages_updated`   | same                                                                                    |
| `pages_processed` | same                                                                                    |
| `pages_skipped`   | same                                                                                    |
| `pages_failed`    | same                                                                                    |

**Steps:** All 5 lists share the same `pages_table` macro. Replace with `new_pages_table(...)`.
Use `renderStep` for step columns, `renderCommonsLink` for Template/New Page.

---

## Phase 4 — Higher Complexity (10+ columns, mixed rendering)

### Step 4a: `add_lang_categories_to_owid_pages/details.html`

| List            | Columns                                                                                             |
| --------------- | --------------------------------------------------------------------------------------------------- |
| `pages_success` | 12 columns: `#`, `OWID Page`, `SVG File`, `Languages`, `Categories Added`, 6 step columns, `Status` |
| `pages_skipped` | same                                                                                                |
| `pages_failed`  | same                                                                                                |

**Steps:** Replace the local `pages_result_table` macro. Needs custom renderers for:

-   `Languages` — join array: `(row) => row.lang_codes?.join(', ') || '-'`
-   `Categories Added` — join array: `(row) => row.categories_added?.join(', ') || '-'`
-   6 step columns using `renderStep`
-   `Status` using `renderStatus`

### Step 4b: `collect_templates_data/details.html` — `pages_updated_table`

| List            | Columns                                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------- |
| `pages_updated` | 10 columns: `#`, `Title`, `Edit`, `Oldest File`, `Newest File`, `Template year`, `Source`, `Slug`, `Files`, `Msg` |
| `pages_skipped` | same                                                                                                              |
| `pages_failed`  | same                                                                                                              |

**Special:** The `Edit` column has a popup link (`pup_window_new`). This needs a custom render
function. Consider embedding the edit URL pattern as a data attribute on the table element.

### Step 4c: `crop_main_files/details.html`

| List              | Columns                                                                   |
| ----------------- | ------------------------------------------------------------------------- |
| `pages_uploaded`  | 12 columns: `#`, `Template`, `File`, `Cropped`, `Compare`, 7 step columns |
| `pages_updated`   | same                                                                      |
| `files_processed` | same                                                                      |
| `pages_skipped`   | same                                                                      |
| `pages_failed`    | same                                                                      |

**Special:** `Cropped` and `Compare` columns are conditional (only shown when `cropped_filename`
exists and status is `uploaded`/`skipped`). Needs conditional render logic in the JS column
definition.

### Step 4d: `update_owid_charts/details.html`

| List             | Columns                                                                          |
| ---------------- | -------------------------------------------------------------------------------- |
| `updated_charts` | 7 columns: `#`, `Slug`, `Min time`, `Max time`, `Years`, `Variable id`, `Source` |
| `failed_charts`  | 3 columns: `#`, `Slug`, `Error`                                                  |
| `skipped_charts` | 3 columns: `#`, `Slug`, `Reason`                                                 |

**Special:** `updated_charts` has nested `.after` fields (e.g., `item.min_time.after`).
External links to `ourworldindata.org/grapher/` and `api.ourworldindata.org`.

---

## Execution Order (Recommended)

| Step   | File                                | Tables                                             | Complexity   |
| ------ | ----------------------------------- | -------------------------------------------------- | ------------ |
| **P1** | `_ajax_table.html`                  | Add `bp_name` param                                | Prerequisite |
| **1**  | `add_svglanguages_template`         | `pages_skipped` only                               | ⭐ Simple    |
| **2**  | `fix_nested_main_files`             | 3 lists                                            | ⭐⭐         |
| **3**  | `download_main_files`               | 3 lists                                            | ⭐⭐         |
| **4**  | `rename_owid_pages`                 | 4 lists                                            | ⭐⭐         |
| **5**  | `collect_templates_data`            | `pages_added` + `pages_updated` + skipped + failed | ⭐⭐⭐       |
| **6**  | `create_owid_pages`                 | 5 lists                                            | ⭐⭐⭐       |
| **7**  | `add_svglanguages_template`         | `pages_processed` + success + failed               | ⭐⭐⭐       |
| **8**  | `add_lang_categories_to_owid_pages` | 3 lists (12 cols)                                  | ⭐⭐⭐⭐     |
| **9**  | `crop_main_files`                   | 5 lists (12 cols)                                  | ⭐⭐⭐⭐     |
| **10** | `update_owid_charts`                | 3 lists (nested data)                              | ⭐⭐⭐⭐     |

---

## Per-File Change Pattern (Template)

For each file, the changes follow this pattern:

1. **Import:** Add

    ```jinja2
    {% from 'jobs_templates/_ajax_templates/_ajax_table.html' import new_pages_table %}
    ```

2. **Remove:** Delete the local Jinja macro (e.g., `pages_table`, `pages_result_table`,
   `result_table`)

3. **Replace:** Swap

    ```jinja2
    {% if result_data.xxx %}
        {{ macro(result_data.xxx, ...) }}
    {% endif %}
    ```

    blocks with:

    ```jinja2
    {% if result_data.xxx %}
    {{ new_pages_table(
        table_title="...",
        job_id=job.id,
        job_type=template_data.job_type,
        list_name="xxx",
        table_headers=[...],
        bp_name='adminpanel.jobs'
    ) }}
    {% endif %}
    ```

4. **JS block:** Add/replace `{% block extra_js %}` with:

    - A `createColumns()` function returning the DataTables column definitions
    - `$(document).ready(function() { initServerTable('table-xxx', createColumns()); ... });`

5. **Remove:** Unused imports from `_skipped_table.html` or `_help_templates` if no longer needed

---

## Detailed Per-File Notes

### 1. `add_lang_categories_to_owid_pages/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `status_icon`, `commons_file_link`, `render_step`, `commons_link`, `pages_skipped_table`, `table_header_to_expand`
-   **Local macros to remove:** `pages_result_table`
-   **Lists:** `pages_success`, `pages_skipped`, `pages_failed`
-   **Special columns:**
    -   `Languages`: `row.lang_codes?.join(', ') || '-'`
    -   `Categories Added`: `row.categories_added?.join(', ') || '-'`
    -   6 step keys: `load_page_text`, `extract_file_name`, `get_languages`, `build_categories`, `check_existing`, `save_page`
    -   `Status`: `renderStatus`
-   **Guard condition:** `{% if data|length > 100 and not expand_all %}` → removed (DataTables handles pagination)

### 2. `add_svglanguages_template/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `render_step`, `pages_skipped_table`, `table_header_to_expand`
-   **Local macros to remove:** `pages_processed_table`
-   **Lists:**
    -   `pages_processed` — step keys: `load_template_text`, `generate_template_text`, `add_template_text`, `save_new_text`
    -   `pages_success` — same columns
    -   `pages_skipped` — 3 cols: `#`, `Title`, `Reason` (uses `pages_skipped_table` macro)
    -   `pages_failed` — same as `pages_processed`
-   **Note:** Remove `pages_skipped_table` import after migrating `pages_skipped`

### 3. `collect_templates_data/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `render_step`, `commons_file_link`, `table_header_to_expand`
-   **Local macros to remove:** `pages_updated_table`
-   **Lists:**
    -   `pages_added` — 2 cols: `#`, `Title`
    -   `pages_updated` — 10 cols: `#`, `Title`, `Edit`, `Oldest File`, `Newest File`, `Template year`, `Source`, `Slug`, `Files`, `Msg`
    -   `pages_skipped` — same as `pages_updated`
    -   `pages_failed` — same as `pages_updated`
-   **Special:** `Edit` column uses `pup_window_new(this, 600, 600)` — embed URL as data attribute

### 4. `create_owid_pages/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `render_step`, `table_header_to_expand`
-   **Local macros to remove:** `pages_table`
-   **Lists:** `pages_created`, `pages_updated`, `pages_processed`, `pages_skipped`, `pages_failed`
-   **Step keys:** `load_template_text`, `create_new_text`, `update_text`, `create_new_page`
-   **Special:** `New Page` column — conditional link (`item.new_page_title` ? link : `-`)

### 5. `crop_main_files/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `render_step`, `commons_file_link`, `table_header_to_expand`
-   **Local macros to remove:** `pages_table`
-   **Lists:** `pages_uploaded`, `pages_updated`, `files_processed`, `pages_skipped`, `pages_failed`
-   **Step keys:** `download`, `crop`, `upload_cropped`, `update_original`, `update_template`, `update_page`, `update_cropped`
-   **Special columns:**
    -   `Template`: `file.template_title.split('/', 1)[1]` — strip prefix
    -   `File`: `commons_file_link(file.original_file, label="File")`
    -   `Cropped`: conditional on `file.cropped_filename` + status
    -   `Compare`: conditional link to `url_for('jobs_utils.compare_crop_files', ...)`

### 6. `download_main_files/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `commons_file_link`
-   **Local macros to remove:** `result_table`
-   **Lists:**
    -   `files_downloaded` — 4 cols: `ID`, `Filename`, `View`, `Size`
    -   `files_skipped` — 4 cols: `ID`, `Template Title`, `Filename`, `Reason`
    -   `files_failed` — 4 cols: `ID`, `Template Title`, `Filename`, `Reason`
-   **Special:** `View` column has `url_for('jobs_utils.serve_download_main_file', filename=file.path)` —
    embed base URL as data attribute

### 7. `fix_nested_main_files/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `commons_file_link`
-   **Local macros to remove:** `result_table`
-   **Lists:**
    -   `pages_success` — 4 cols: `ID`, `Title`, `Oldest File`, `Result`
    -   `pages_failed` — 4 cols: `ID`, `Title`, `Oldest File`, `Reason`
    -   `pages_skipped` — 4 cols: `ID`, `Title`, `Oldest File`, `Reason`
-   **Simplest table shape** — no step rendering needed

### 8. `rename_owid_pages/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `commons_link`, `table_header_to_expand`
-   **Local macros to remove:** `pages_table`
-   **Lists:** `pages_renamed`, `pages_skipped`, `pages_redirected`, `pages_failed`
-   **Special:**
    -   `pages_redirected` has an info alert div — keep it above the table
    -   Column headers change based on section type (old title / old title now redirect)
    -   Use a single column definition with conditional titles via function parameters

### 9. `update_owid_charts/details.html`

-   **Extends:** `base_details_admin.html`
-   **Current imports:** `card_header`, `stats_card`, `table_header_to_expand`
-   **Local macros to remove:** None (all inline)
-   **Lists:**
    -   `updated_charts` — 7 cols: `#`, `Slug`, `Min time`, `Max time`, `Years`, `Variable id`, `Source`
    -   `failed_charts` — 3 cols: `#`, `Slug`, `Error`
    -   `skipped_charts` — 3 cols: `#`, `Slug`, `Reason`
-   **Special:** `updated_charts` nested data:
    -   `item.min_time.after` or `item.new_min_time`
    -   `item.max_time.after` or `item.new_max_time`
    -   `item.len_years.after` or `item.new_len_years`
    -   `item.variable_id.after` or `item.owid_variable_id`
    -   `item.source.after` or fallback

---

## Testing Checklist

After migrating each file:

-   [ ] Page loads without errors
-   [ ] Table displays data from AJAX endpoint
-   [ ] Pagination works (shows correct total count)
-   [ ] Search/filter works across visible columns
-   [ ] Sort works on orderable columns
-   [ ] Links render correctly (commons links, external links, edit links)
-   [ ] Step badges render correctly (success/danger/secondary)
-   [ ] Stats cards above tables still show correct counts
-   [ ] `expand_all` parameter still works (or is no longer needed)
-   [ ] No JS console errors
