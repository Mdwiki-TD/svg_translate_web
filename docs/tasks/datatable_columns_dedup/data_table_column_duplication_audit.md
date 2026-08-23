# DataTable Column-Generation Duplication — Unified Report

> This report merges two independent audits of the column-generation code used by every
> `initServerTable(...)` call in the repository (`data_table_column_duplication_audit.md` and
> `datatable_columns_dedup_report.md`). Both audits scanned the same 11 `details.html` templates
> under `src/templates/jobs_templates/` and the shared JS in `src/static/js/data_table_ajax/`.
> No source files were modified in either audit — this is analysis only.

---

## 1. Scope & Agreed Facts

Both audits agree on the following core findings:

-   **11 HTML templates** call `initServerTable(...)` — `initServerTable` itself is already centralized
    (single definition in `src/static/js/data_table_ajax/table.js`) and is **not** duplicated.
-   **16 distinct column-generation functions** are defined, one inline `<script>` per template inside
    `{% block extra_js %}`. None live in a shared module today.
-   Because each template renders a separate page, functions with the _same name_ (`createColumns`,
    `createTableColumns`, `createUpdatedColumns`, `createSkippedColumns`) do not collide at runtime —
    but they are still duplicated _logic_ and a maintainability hazard.
-   **One exact, byte-identical duplicate**: `renderOwidTitle` (`collect_templates_data`) and
    `renderOwidTemplate` (`create_owid_pages`) have identical bodies and should be merged into a single
    shared helper.
-   The **`#` row-index column** (`{ data: null, render: (d,t,r,meta) => meta.row + 1 }`) is the single
    biggest source of repetition, copy-pasted across nearly every column function except the two
    `download_main_files` functions, which intentionally use `data: 'template_id'` (a stable DB id, not
    a row index) and must **not** be folded into the same helper.
-   Shared render helpers already exist and are correctly reused (not duplicated):
    `renderStatus`, `renderWikiLink`, `renderCommonsLink`, `renderCommonsFileLink` /
    `renderCommonsFileLinkShort`, `renderStep`, `diffLink`.

### Note on count discrepancies between the two source audits

The two audits count the repeated `#` index block slightly differently (one says "17 of 16"
occurrences — an internal inconsistency in that document — the other says "9 of 10" in a section
header but then lists it across 11 functions elsewhere). Reconciled against both functions
inventories: **14 of the 16 functions** contain the `meta.row + 1` index block (all except the two
`download_main_files` functions, which use `template_id`). Treat "14" as the reliable number for
planning; the "17" and "10" figures in the source documents appear to be counting/labeling slips
rather than substantive disagreements.

---

## 2. Full Inventory (merged)

| #   | File / Function                                                                                                              | Cols | Tables Used By                                                              | Notes                                                       |
| --- | ---------------------------------------------------------------------------------------------------------------------------- | ---- | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 1   | `public/extract_files_translations/details.html`<br>`createTableColumns(show_download, show_nested, err_colmn, show_status)` | 7    | files_success, files_processed, files_failed (+skipped, commented out)      | `#`, File, Status, Download, Translations, Languages, Error |
| 2   | `public/copy_svg_langs/details.html`<br>`createTableColumns(show_download, show_nested, err_colmn, show_status)`             | 10   | files_success, files_processed, files_skipped, files_failed                 | Same signature as #1, step-based middle columns             |
| 3   | `admin/crop_main_files/details.html`<br>`createColumns()`                                                                    | 12   | pages_uploaded, pages_updated, files_processed, pages_skipped, pages_failed | Uses local `renderCropTemplate`                             |
| 4   | `admin/add_svglanguages_template/details.html`<br>`createProcessedColumns()`                                                 | 6    | pages_processed, pages_success, pages_failed                                | Template + text/save steps                                  |
| 5   | `admin/add_svglanguages_template/details.html`<br>`createSkippedColumns()`                                                   | 3    | pages_skipped                                                               | `#`, Title, Reason (`reason\|\|error\|\|msg`)               |
| 6   | `admin/update_owid_charts/details.html`<br>`createUpdatedColumns()`                                                          | 7    | updated_charts                                                              | OWID chart field diffs                                      |
| 7   | `admin/update_owid_charts/details.html`<br>`createFailedColumns()`                                                           | 3    | failed_charts                                                               | `#`, Slug, Error                                            |
| 8   | `admin/update_owid_charts/details.html`<br>`createSkippedColumns()`                                                          | 3    | skipped_charts                                                              | `#`, Slug, Reason (`skip_reason`)                           |
| 9   | `admin/collect_templates_data/details.html`<br>`createAddedColumns()`                                                        | 2    | pages_added                                                                 | `#`, Title (via `renderOwidTitle`)                          |
| 10  | `admin/collect_templates_data/details.html`<br>`createUpdatedColumns()`                                                      | 10   | pages_updated, pages_skipped, pages_failed                                  | Template file/year/source fields                            |
| 11  | `admin/rename_owid_pages/details.html`<br>`createColumns(old_title_label, new_title_label)`                                  | 4    | pages_renamed, pages_skipped, pages_redirected, pages_failed                | Only parameterized function                                 |
| 12  | `admin/create_owid_pages/details.html`<br>`createColumns()`                                                                  | 7    | pages_created, pages_updated, pages_processed, pages_skipped, pages_failed  | Uses local `renderOwidTemplate`                             |
| 13  | `admin/download_main_files/details.html`<br>`createDownloadedColumns()`                                                      | 4    | files_downloaded                                                            | `#` = `template_id` (not row index)                         |
| 14  | `admin/download_main_files/details.html`<br>`createResultColumns()`                                                          | 4    | files_skipped, files_failed                                                 | `#` = `template_id`; Reason (`reason\|\|error`)             |
| 15  | `admin/add_lang_categories_to_owid_pages/details.html`<br>`createColumns()`                                                  | 12   | pages_success, pages_skipped, pages_failed                                  | Language/category step chain                                |
| 16  | `admin/fix_nested_main_files/details.html`<br>`createTableColumns(show_reason, show_result)`                                 | 5    | pages_success, pages_failed, pages_skipped                                  | Conditional Result/Reason columns                           |

**Total: 16 functions across 11 files.**

---

## 3. Duplicate / Redundant Patterns

### 3.1 `renderOwidTitle` ↔ `renderOwidTemplate` — exact duplicate (High confidence)

Byte-identical bodies in `collect_templates_data` and `create_owid_pages`. **Merge into one
shared helper** (`renderOwidTitle`) in `macros.js`; delete both local copies.

### 3.2 `#` row-index column — repeated in 14 of 16 functions (High confidence)

Exact same object literal (`{ data: null, title: '#', render: (d,t,r,meta) => meta.row + 1 }`,
sometimes as a named function instead of an arrow). **Extract to `indexColumn()`** in `macros.js`.
The two `download_main_files` functions must keep `data: 'template_id'` — do not merge these.

### 3.3 "Reason / error message" column — duplicated 5× with 4 slightly different fallback chains (Medium)

Appears in `add_svglanguages_template` (skipped), `update_owid_charts` (skipped), `download_main_files`
(result), `fix_nested_main_files`, and `collect_templates_data` ("Msg"), each reading a different
combination of `reason || error || msg || message`. **Extract a parameterized `messageColumn(title,
dataKey)`** that checks all four fields in a stable order.

### 3.4 "Title" column via `renderCommonsLink` — duplicated 6× (Medium)

Same render function, only `data` key and `title` label differ, across `add_svglanguages_template`,
`collect_templates_data`, `rename_owid_pages` (×2), `download_main_files`, `add_lang_categories`, and
`fix_nested_main_files`. **Extract `titleColumn(dataKey, label)`.**

### 3.5 "File" link column — near-duplicate 4× (Medium)

`renderCommonsFileLink` and `renderCommonsFileLinkShort` differ only in default label and are used
across `extract`, `copy`, `crop`, `download`, and `fix_nested`. **Unify into one renderer with a
`label` parameter**, then extract `fileLinkColumn(dataKey, label)`.

### 3.6 `createTableColumns` (extract) ↔ `createTableColumns` (copy) — high structural overlap (Medium)

Identical signature and an identical leading/trailing scaffold (`#`, File, Status, Download, Error);
only the middle columns differ (extract: Translations/Languages; copy: step-based Nested/Inject/
Upload/Translations). **Extract `baseFileColumns(opts)`**, with each page appending its own middle
columns. Do not collapse into a single unconditional function — the middle columns are genuinely
different.

### 3.7 `createSkippedColumns` (svglang) ↔ `createSkippedColumns` (charts) — same shape, different data (Medium)

Both are `#` + link column + Reason, but the link entity (Commons title vs. OWID slug) and the reason
field (`reason||error||msg` vs. `skip_reason`) differ. **Parameterize into a shared
`skippedColumns({ linkData, linkRender, reasonData })`.**

### 3.8 `add_svglanguages_template::createProcessedColumns` ↔ `create_owid_pages::createColumns` — partial overlap (Medium)

Both share a Template + "Load Text" + "Generate Text" trio that becomes structurally identical once
3.1 is fixed. **Extract `templateStepColumns()`** for the shared trio; each page appends its
remaining steps.

### 3.9 `update_owid_charts`'s three functions share a Slug column (Medium)

`createUpdatedColumns`, `createFailedColumns`, and `createSkippedColumns` in the same file all start
with `#` + `Slug → renderOwidSlug`. **Extract `slugColumn()`**; each function keeps only its
differing tail columns.

### 3.10 Name collisions — same identifier, different columns (Low confidence — naming only, not a logic merge)

-   `createColumns()` defined in 4 files (`crop_main_files`, `rename_owid_pages`, `create_owid_pages`,
    `add_lang_categories_to_owid_pages`) — all materially different column sets.
-   `createUpdatedColumns()` defined in `update_owid_charts` and `collect_templates_data` — chart data
    vs. template data, unrelated.
-   `createTableColumns()` defined in `extract`, `copy`, and `fix_nested` — different signatures/columns.
-   `createSkippedColumns()` defined in `add_svglanguages_template` and `update_owid_charts` — see 3.7.

**Recommendation: rename, do not merge.** e.g. `cropColumns()`, `renameColumns()`,
`createOwidPagesColumns()`, `collectTemplateUpdatedColumns()`, `fixNestedColumns()`.

---

## 4. Functions That Should NOT Be Merged

1. The four `createColumns()` implementations — despite the shared name, their column sets are
   materially different (crop/compare steps vs. new/create page vs. SVG/language/category steps vs.
   old/new title). Rename only.
2. `createUpdatedColumns` (charts) vs. `createUpdatedColumns` (templates) — unrelated domains
   (chart time/variable diffs vs. template file/year/source data).
3. `createSkippedColumns` (svglang) vs. `createSkippedColumns` (charts) — different link entity and
   reason field; parameterize, don't force into one literal body.
4. `download_main_files`'s `#` column (`template_id`) — a stable database id, not a row index; keep
   separate from `indexColumn()`, or add an explicit `idIndexColumn('template_id')` variant if wanted.
5. `createTableColumns` (fix_nested) vs. extract/copy — different signature and column set; refactor
   into a shared naming/skeleton convention only if useful, not a direct merge.

---

## 5. Proposed Target Structure

Both source audits converge on the same underlying idea — centralize repeated column _shapes_ and
renderers into shared modules — but propose different levels of granularity. This unified
recommendation adopts the more granular breakdown (closer to `datatable_columns_dedup_report.md`)
since it removes more duplication, while keeping the simpler grouping from
`data_table_column_duplication_audit.md` as an acceptable lighter-weight alternative.

**`src/static/js/data_table_ajax/macros.js`** (already shared/global) — add:

-   `indexColumn(title = '#')` — the row-index cell (§3.2)
-   `titleColumn(dataKey, label)` — Commons-link title cell (§3.4)
-   `fileLinkColumn(dataKey, label)` — unified file-link cell, replacing the
    `renderCommonsFileLink`/`renderCommonsFileLinkShort` split (§3.5)
-   `messageColumn(title, dataKey)` — reason/error fallback cell (§3.3)
-   `slugColumn()` — OWID slug link cell (§3.9)
-   `templateColumn(dataKey, label)` — OWID template-title cell, replacing `renderOwidTemplate`/
    `renderOwidTitle` (§3.1)

**New shared module `src/static/js/data_table_ajax/column_helpers.js`** (loaded in `base.html`
alongside `table.js`/`macros.js`) — add:

-   `baseFileColumns(opts)` — the common `#`/File/Status/Download/Error scaffold for extract & copy (§3.6)
-   `templateStepColumns(opts)` — the shared Template/Load Text/Generate Text trio (§3.8)
-   `skippedColumns({ linkData, linkRender, reasonData })` — covers svglang & charts skipped tables (§3.7)
-   Optional: `idIndexColumn(dataKey)` for `download_main_files`'s `template_id` index variant

**Per-page templates:** keep only thin callers that pass page-specific data keys/renderers to the
shared helpers. Rename the generic, colliding names (`createColumns`, `createTableColumns`,
`createUpdatedColumns`, `createSkippedColumns`) to page-specific names for clarity (§3.10). Genuinely
unique page-local renderers (`renderCropTemplate`, `renderOwidSlug`, `renderOwidVariableLink`) stay
local.

This keeps `initServerTable` as the single wiring point, centralizes shared column shape/renderers,
and removes name collisions without merging behaviorally distinct tables.

---

## 6. Migration Impact

| File                                             | Action                                                                                                                                        |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `macros.js`                                      | Add `indexColumn`, `titleColumn`, `fileLinkColumn`, `messageColumn`, `slugColumn`, `templateColumn`; unify file-link and OWID-title renderers |
| New `column_helpers.js`                          | Add `baseFileColumns`, `templateStepColumns`, `skippedColumns`                                                                                |
| `base.html`                                      | Add `<script>` tag loading `column_helpers.js` before templates that use it                                                                   |
| `extract_files_translations/details.html`        | Replace `createTableColumns` with `baseFileColumns` + extras                                                                                  |
| `copy_svg_langs/details.html`                    | Replace `createTableColumns` with `baseFileColumns` + extras                                                                                  |
| `crop_main_files/details.html`                   | `createColumns` → `indexColumn` + shared renderers; rename function                                                                           |
| `add_svglanguages_template/details.html`         | `createProcessedColumns`/`createSkippedColumns` → shared builders                                                                             |
| `update_owid_charts/details.html`                | 3 functions → `indexColumn` + `slugColumn` + `messageColumn`                                                                                  |
| `collect_templates_data/details.html`            | 2 functions → shared builders; drop local `renderOwidTitle`                                                                                   |
| `rename_owid_pages/details.html`                 | `createColumns` → `indexColumn` + `titleColumn`; rename function                                                                              |
| `create_owid_pages/details.html`                 | `createColumns` → shared template builders; drop local `renderOwidTemplate`; rename function                                                  |
| `download_main_files/details.html`               | 2 functions → `titleColumn`/`messageColumn`, keep `template_id` index                                                                         |
| `add_lang_categories_to_owid_pages/details.html` | `createColumns` → `indexColumn` + `titleColumn` + shared file/step columns; rename function                                                   |
| `fix_nested_main_files/details.html`             | `createTableColumns` → `indexColumn` + `titleColumn` + `fileLinkColumn` + `messageColumn`; rename function                                    |

**None of the 11 `initServerTable(...)` call sites themselves need to change** — table IDs and call
counts stay the same; only the column-function bodies are refactored.

---

## 7. Summary of Removals / Merges

| Category                                                                                                | Occurrences    | Action                                  |
| ------------------------------------------------------------------------------------------------------- | -------------- | --------------------------------------- |
| Row-`#` index column bodies                                                                             | 14             | → 1 shared `indexColumn()`              |
| Reason/error message column bodies                                                                      | 5              | → 1 shared `messageColumn()`            |
| Title column via `renderCommonsLink`                                                                    | 6              | → 1 shared `titleColumn()`              |
| File link column bodies                                                                                 | 4              | → 1 shared `fileLinkColumn()`           |
| `renderOwidTemplate` ≡ `renderOwidTitle`                                                                | 2 (exact dup)  | → 1 function                            |
| `renderCommonsFileLink` / `renderCommonsFileLinkShort`                                                  | 2              | → 1 unified renderer                    |
| `extract` vs. `copy` base columns                                                                       | 2              | → shared `baseFileColumns()`            |
| Template/Load Text/Generate Text trio                                                                   | 2              | → shared `templateStepColumns()`        |
| `createSkippedColumns` ×2                                                                               | 2              | → shared `skippedColumns()`             |
| Name collisions (`createColumns`, `createTableColumns`, `createUpdatedColumns`, `createSkippedColumns`) | 11 definitions | Rename to unique, domain-specific names |

**Estimated net effect:** roughly 30 near-identical inline column blocks collapse into ~8–9 reusable
shared builders, removing on the order of 85–100+ lines of duplicated configuration and eliminating
all 4 sets of colliding function names — without altering any table's visible behavior.

---

## 8. Verification Checklist

-   [ ] All 11 `initServerTable(` consumers accounted for.
-   [ ] All 16 column-generation functions accounted for.
-   [ ] Every duplicate/near-duplicate above reviewed against real behavior before merging.
-   [ ] Call sites identified before removal — no `initServerTable` argument changes required.
-   [ ] Behaviorally distinct functions (§4) are **not** incorrectly merged.
-   [ ] `download_main_files`'s `template_id` index is preserved, not folded into `indexColumn()`.
-   [ ] New shared helpers load correctly via `base.html` before any template that uses them.
-   [ ] Visual/behavioral regression check on all 11 job detail pages after refactor (column order,
        visibility flags, and `#`/index values preserved).

---

## 9. Conclusion

Both source audits reach the same conclusion by different routes: the 16 column-generation functions
across 11 templates contain a large amount of copy-pasted (not just similarly-named) logic — most
notably one exact-duplicate helper and a row-index block repeated 14 times — that can be consolidated
into 6 shared cell builders in `macros.js` plus 3 shared table-shape builders in a new
`column_helpers.js`, with zero required changes to `initServerTable` call sites and zero risk to the
four groups of functions that only share a _name_, not behavior.
