# DataTable Column Duplication Audit

> Static analysis of column-generation code behind every `initServerTable(` call in the repository.
> Scope: all `.html` templates under `src/templates/`. Shared JS helpers live in
> `src/static/js/data_table_ajax/table.js` (`initServerTable`) and `macros.js` (render helpers).
> No source files were modified — this is an analysis/report only.

## Executive Summary

-   **Matching HTML files (callers of `initServerTable(`):** 11
-   **Discovered column-generation functions (definition sites):** 16
    -   16 inline `<script>` functions declared inside `{% block extra_js %}` of the 11 templates.
    -   These are page-scoped globals (each template renders a separate document), so identical names
        such as `createColumns` / `createTableColumns` / `createUpdatedColumns` do **not** collide at
        runtime. They are, however, duplicated _logic_ that should be consolidated.
-   **Exact duplicates:** 1 pair of render helpers (`renderOwidTitle` ≡ `renderOwidTemplate`).
-   **Likely duplicates / strong overlap:** 3 areas — the `#` index column (17 repetitions), the two
    `createTableColumns` (extract vs copy), and the two `createSkippedColumns` (svglang vs charts).
-   **Recommended merges:** 4 (1 exact helper merge + 3 refactors into shared helpers).
-   **Recommended removals:** 0 functions can be fully _deleted_ today beyond folding into a shared
    helper during the refactors above. After consolidation, several per-page wrappers become thin
    callers of shared helpers (candidates for eventual removal, but kept during migration).
-   **Functions recommended for removal (post-migration):** the per-page duplicate wrappers once the
    shared helpers exist; tracked in the cleanup section.

Note: `initServerTable(...)` itself is already centralized and shared (one definition in
`src/static/js/data_table_ajax/table.js`). All duplication is in the _column_ definitions, not in the
table wiring.

## HTML Usage Inventory

| HTML File                                                                                     |                                                                      `initServerTable` Call(s) | Column Function(s)                                                                              |
| --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------: | ----------------------------------------------------------------------------------------------- |
| `src/templates/jobs_templates/public/extract_files_translations/details.html`                 |                        4 (success, processed, skipped[commented], failed) @L177,L183,L193,L202 | `createTableColumns(...)` (L117)                                                                |
| `src/templates/jobs_templates/public/copy_svg_langs/details.html`                             |                                   4 (success, processed, skipped, failed) @L219,L223,L232,L240 | `createTableColumns(...)` (L141)                                                                |
| `src/templates/jobs_templates/admin_templates/crop_main_files/details.html`                   |     5 (pages_uploaded, pages_updated, files_processed, pages_skipped, pages_failed) @L207–L211 | `createColumns()` (L108)                                                                        |
| `src/templates/jobs_templates/admin_templates/add_svglanguages_template/details.html`         |                     4 (pages_processed, pages_success, pages_failed, pages_skipped) @L155–L159 | `createProcessedColumns()` (L82), `createSkippedColumns()` (L128)                               |
| `src/templates/jobs_templates/admin_templates/update_owid_charts/details.html`                |                                   3 (updated_charts, failed_charts, skipped_charts) @L223–L225 | `createUpdatedColumns()` (L85), `createFailedColumns()` (L175), `createSkippedColumns()` (L201) |
| `src/templates/jobs_templates/admin_templates/collect_templates_data/details.html`            |                         4 (pages_added, pages_updated, pages_skipped, pages_failed) @L242–L245 | `createAddedColumns()` (L115), `createUpdatedColumns()` (L135)                                  |
| `src/templates/jobs_templates/admin_templates/rename_owid_pages/details.html`                 | 4 (pages_renamed, pages_skipped, pages_redirected[variant], pages_failed) @L132,L133,L134,L141 | `createColumns(...)` (L96)                                                                      |
| `src/templates/jobs_templates/admin_templates/create_owid_pages/details.html`                 |      5 (pages_created, pages_updated, pages_processed, pages_skipped, pages_failed) @L168–L172 | `createColumns()` (L118)                                                                        |
| `src/templates/jobs_templates/admin_templates/download_main_files/details.html`               |                                   3 (files_downloaded, files_skipped, files_failed) @L138–L140 | `createDownloadedColumns()` (L74), `createResultColumns()` (L107)                               |
| `src/templates/jobs_templates/admin_templates/add_lang_categories_to_owid_pages/details.html` |                                      3 (pages_success, pages_skipped, pages_failed) @L152–L154 | `createColumns()` (L70)                                                                         |
| `src/templates/jobs_templates/admin_templates/fix_nested_main_files/details.html`             |                                 3 (pages_success, pages_failed, pages_skipped) @L108,L115,L122 | `createTableColumns(...)` (L62)                                                                 |

## Column Function Inventory

| Function                                                                 | File                                                                | Used By (tables)                                                            | Columns Produced                                                                                                                     | Notes                                                                    |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ | --- | ------- | --- | ----- |
| `createTableColumns(show_download, show_nested, err_colmn, show_status)` | `public/extract_files_translations/details.html:117`                | files_success, files_processed, files_failed (+skipped commented)           | `#`, File, Status, Download, Translations, Languages, Error                                                                          | Conditional/visible flags; params toggling column visibility.            |
| `createTableColumns(show_download, show_nested, err_colmn, show_status)` | `public/copy_svg_langs/details.html:141`                            | files_success, files_processed, files_skipped, files_failed                 | `#`, File, Status, Download, Nested tags, Translations Inserted, Translations Updated, Inject, Upload, Error                         | Same signature/leading+trailing as extract, different middle columns.    |
| `createColumns()`                                                        | `admin_templates/crop_main_files/details.html:108`                  | pages_uploaded, pages_updated, files_processed, pages_skipped, pages_failed | `#`, Template, File, Cropped, Compare, Download, Crop, Upload, Update File, Update Template, Update Page, Update Cropped             | Uses page-local `renderCropTemplate`; conditional Cropped/Compare links. |
| `createProcessedColumns()`                                               | `admin_templates/add_svglanguages_template/details.html:82`         | pages_processed, pages_success, pages_failed                                | `#`, Template, Load Text, Generate Text, Add Text, Save Page                                                                         | Uses page-local `renderWikiLink`/`WIKIDOMAIN`.                           |
| `createSkippedColumns()`                                                 | `admin_templates/add_svglanguages_template/details.html:128`        | pages_skipped                                                               | `#`, Title, Reason                                                                                                                   | Link via `renderCommonsLink`; reason = `reason                           |     | error   |     | msg`. |
| `createUpdatedColumns()`                                                 | `admin_templates/update_owid_charts/details.html:85`                | updated_charts                                                              | `#`, Slug, Min time, Max time, Years, Variable id, Source                                                                            | OWID chart-field diff rendering (`*.after`/`new_*`).                     |
| `createFailedColumns()`                                                  | `admin_templates/update_owid_charts/details.html:175`               | failed_charts                                                               | `#`, Slug, Error                                                                                                                     | Slug link via `renderOwidSlug`.                                          |
| `createSkippedColumns()`                                                 | `admin_templates/update_owid_charts/details.html:201`               | skipped_charts                                                              | `#`, Slug, Reason                                                                                                                    | Slug link via `renderOwidSlug`; reason = `skip_reason`.                  |
| `createAddedColumns()`                                                   | `admin_templates/collect_templates_data/details.html:115`           | pages_added                                                                 | `#`, Title                                                                                                                           | Link via `renderOwidTitle`.                                              |
| `createUpdatedColumns()`                                                 | `admin_templates/collect_templates_data/details.html:135`           | pages_updated, pages_skipped, pages_failed                                  | `#`, Title, Edit, Oldest File, Newest File, Template year, Source, Slug, Files, Msg                                                  | OWID _template_ fields; Edit popup button.                               |
| `createColumns(old_title_label, new_title_label)`                        | `admin_templates/rename_owid_pages/details.html:96`                 | pages_renamed, pages_skipped, pages_redirected(variant), pages_failed       | `#`, Old title, New title, Message                                                                                                   | Parameterized labels used for 1 variant; links via `renderCommonsLink`.  |
| `createColumns()`                                                        | `admin_templates/create_owid_pages/details.html:118`                | pages_created, pages_updated, pages_processed, pages_skipped, pages_failed  | `#`, Template, New Page, Load Text, Generate Text, Update Page, Create Page                                                          | Uses page-local `renderOwidTemplate`.                                    |
| `createDownloadedColumns()`                                              | `admin_templates/download_main_files/details.html:74`               | files_downloaded                                                            | `#`(=`template_id`), Filename, View, Size                                                                                            | Index is `data:'template_id'` (NOT meta.row). View popup link.           |
| `createResultColumns()`                                                  | `admin_templates/download_main_files/details.html:107`              | files_skipped, files_failed                                                 | `#`(=`template_id`), Template Title, Filename, Reason                                                                                | Index is `data:'template_id'`. Reason = `reason                          |     | error`. |
| `createColumns()`                                                        | `admin_templates/add_lang_categories_to_owid_pages/details.html:70` | pages_success, pages_skipped, pages_failed                                  | `#`, OWID Page, SVG File, Languages, Categories Added, Load Text, Extract SVG, Get Langs, Build Cats, Check Exist, Save Page, Status | Uses `renderStatus` + `renderCommonsFileLinkShort`.                      |
| `createTableColumns(show_reason, show_result)`                           | `admin_templates/fix_nested_main_files/details.html:62`             | pages_success, pages_failed, pages_skipped                                  | `#`, Title, Oldest File, Result, Reason                                                                                              | Conditional Result/Reason via `visible:` flags.                          |

**Shared render helpers** (already centralized in `src/static/js/data_table_ajax/macros.js`):
`renderStatus`, `renderWikiLink`, `renderCommonsFileLink`, `renderCommonsLink`,
`renderCommonsFileLinkShort`, `renderStep`, `diffLink`. These are reused by the functions above and
are correctly DRY.

**Page-local render helpers** (declared inside individual templates):
`renderCropTemplate` (crop_main_files:99), `renderOwidSlug` (update_owid_charts:66),
`renderOwidVariableLink` (update_owid_charts:76), `renderOwidTitle` (collect_templates_data:106),
`renderOwidTemplate` (create_owid_pages:108).

## Duplicate / Merge Candidates

### `renderOwidTitle` ↔ `renderOwidTemplate`

-   **Confidence:** High
-   **Files:**
    -   `src/templates/jobs_templates/admin_templates/collect_templates_data/details.html:106`
    -   `src/templates/jobs_templates/admin_templates/create_owid_pages/details.html:108`
-   **HTML consumers:** `createAddedColumns()` (collect) and `createColumns()` (create_owid) — each
    is used in the respective detail page's DataTable columns.
-   **Similarity:** **Exact duplicate.** Both have identical bodies:
    ```js
    function renderOwidTitle(title) {
        function renderOwidTemplate(title) {
            if (!title) return "-";
            if (!title) return "-";
            const display = title.replace(/^Template:OWID\//, "");
            return renderWikiLink(WIKIDOMAIN, title, display);
        }
    }
    ```
-   **Differences:** None (function name only; behavior identical).
-   **Recommendation:** Merge into a single shared helper in `macros.js` (e.g. `renderOwidTitle`),
    and have both pages call it. Page-local `WIKIDOMAIN` is already available on both pages, and
    `macros.js` is loaded globally via `src/templates/base.html:52`.
-   **Required call-site changes:**
    -   Remove the local definitions from both templates.
    -   In `create_owid_pages/details.html`, replace `render: renderOwidTemplate` with
        `render: renderOwidTitle` (or alias).
-   **Removal candidate:** Yes (both local copies).

---

### `#` index column (`meta.row + 1`) — repeated configuration block

-   **Confidence:** High
-   **Files:** Repeated in 17 of the 16 column functions (download uses `data:'template_id'` instead).
    Definition sites include every `createTableColumns`/`createColumns`/`createProcessedColumns`/
    `createSkippedColumns`/`createAddedColumns`/`createUpdatedColumns`/`createFailedColumns` function
    listed above except `createDownloadedColumns`/`createResultColumns` (which use `template_id`).
-   **HTML consumers:** All 11 HTML files.
-   **Similarity:** Exact repeated block:
    ```js
    { data: null, title: '#',
      render: function (data, type, row, meta) { return meta.row + 1; } }
    ```
    (Some copies use a one-line arrow variant for the render; functionally identical.)
-   **Differences:** None behaviorally. The two download functions use `data: 'template_id'` for the
    `#` column instead — semantically different (stable DB id vs. row index) and should **not** be
    force-merged with the meta.row variant; see "Functions That Should Not Be Merged".
-   **Recommendation:** Refactor into a shared helper `indexColumn()` (returning the object above) in
    `macros.js`, and have each column function start with `indexColumn(),` as its first element.
-   **Required call-site changes:** Replace the inline `#` block with `indexColumn()` in 14 functions
    (15 occurrences: extract, copy, crop, add_svglang processed, add_svglang skipped, update updated,
    update failed, update skipped, collect added, collect updated, rename, create_owid, add_lang,
    fix_nested).
-   **Removal candidate:** N/A (it is a config block, not a named function).

---

### `createTableColumns` (extract) ↔ `createTableColumns` (copy)

-   **Confidence:** Medium
-   **Files:**
    -   `src/templates/jobs_templates/public/extract_files_translations/details.html:117`
    -   `src/templates/jobs_templates/public/copy_svg_langs/details.html:141`
-   **HTML consumers:** the two public job detail pages (4 tables each).
-   **Similarity:** Identical signature `(show_download, show_nested, err_colmn, show_status)` and
    identical leading group (`#`, File, Status, Download) and trailing group (`Error`). Both toggle
    column visibility via the boolean params.
-   **Differences:**
    -   extract middle: `Translations` (row.steps.load_mapping.details.new), `Languages` (array join).
    -   copy middle: `Nested tags` (renderStep on steps.nested), `Translations Inserted`,
        `Translations Updated`, `Inject`, `Upload` (all renderStep-based).
    -   extract's "Translations"/"Languages" are _not_ step-based; copy's middle is entirely
        step-based with `orderable:false`. Different data sources → not behaviorally identical.
-   **Recommendation:** Refactor into a shared base builder, e.g.
    `buildFileTableColumns(extraMiddleCols, opts)` that emits the common `#/File/Status/Download/Error`
    scaffold and accepts a page-specific middle-column array. Extract and copy become thin callers.
    Do **not** collapse into a single unconditional function (the middle columns are genuinely
    different).
-   **Required call-site changes:** Keep the four `initServerTable` calls in each file; only change
    the function bodies to delegate to the shared base. The currently-commented skipped call in
    extract can be left as-is.
-   **Removal candidate:** No (become thin wrappers).

---

### `createSkippedColumns` (add_svglanguages) ↔ `createSkippedColumns` (update_owid_charts)

-   **Confidence:** Medium
-   **Files:**
    -   `src/templates/jobs_templates/admin_templates/add_svglanguages_template/details.html:128`
    -   `src/templates/jobs_templates/admin_templates/update_owid_charts/details.html:201`
-   **HTML consumers:** `pages_skipped` (svglang) and `skipped_charts` (charts).
-   **Similarity:** Same shape: `#`, a wiki/slug link column, and a Reason column.
-   **Differences:**
    -   Link column: svglang uses `data:'title'` + `renderCommonsLink`; charts uses `data:'slug'` +
        `renderOwidSlug`. Different entities (Commons page vs OWID grapher slug).
    -   Reason: svglang `row.reason || row.error || row.msg`; charts `row.skip_reason`. Different field
        name.
-   **Recommendation:** Parameterize into a shared helper `skippedColumns({linkData, linkRender,
reasonData})` (or accept a renderer that reads the right field). The two pages supply different
    data keys/renderers. Keeps behavior identical while removing duplication.
-   **Required call-site changes:** Replace both local definitions with calls to the shared helper,
    passing the appropriate data key + renderer. No `initServerTable` call sites change.
-   **Removal candidate:** No (become thin callers).

---

### Naming collisions: same function name, different behavior

-   **Confidence:** Low (naming, not logic)
-   **Files / names:**
    -   `createColumns` defined in **four** files: crop_main_files:108, rename_owid_pages:96,
        create_owid_pages:118, add_lang_categories_to_owid_pages:70 — each with a **different** column
        set (only rename's is parameterized).
    -   `createUpdatedColumns` defined in update_owid_charts:85 and collect_templates_data:135 — totally
        different columns (charts vs templates).
    -   `createTableColumns` defined in extract:117, copy:141, fix_nested:62 — different columns/signature.
-   **HTML consumers:** their respective pages.
-   **Similarity:** Names only.
-   **Differences:** Column contents differ entirely (documented in the Column Function Inventory).
-   **Recommendation:** **Do not merge.** Rename each to a page-specific, descriptive name to remove
    reader confusion (e.g. `cropColumns()`, `renameColumns()`, `createOwidPagesColumns()`,
    `collectTemplateUpdatedColumns()`, `fixNestedColumns()`). This is a clarity/refactor action, not a
    logic merge.
-   **Required call-site changes:** Rename within each template's `$(document).ready` block
    (1–5 calls each).
-   **Removal candidate:** No.

## Recommended Consolidation

| Priority | Current Functions                                                         | Canonical Function                                          | Action                                    | Confidence |
| -------- | ------------------------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------- | ---------- |
| 1        | `renderOwidTitle` (collect:106), `renderOwidTemplate` (create_owid:108)   | `renderOwidTitle` in `macros.js`                            | Merge / Remove both locals                | High       |
| 2        | `#` index column block in 14 functions                                    | `indexColumn()` in `macros.js`                              | Refactor into shared helper               | High       |
| 3        | `createSkippedColumns` (svglang:128), `createSkippedColumns` (charts:201) | `skippedColumns({...})` in a shared `data_tables.js` helper | Refactor / parameterize                   | Medium     |
| 4        | `createTableColumns` (extract:117), `createTableColumns` (copy:141)       | `buildFileTableColumns(extra, opts)` in shared helper       | Refactor into shared base + thin wrappers | Medium     |
| 5        | `createColumns` ×4, `createUpdatedColumns` ×2, `createTableColumns` ×3    | Keep separate, rename to page-specific names                | Refactor (rename) for clarity             | Low        |

Legend: **Merge** = fold duplicate into one; **Remove** = delete the duplicate copy;
**Keep separate** = do not combine; **Refactor into shared helper** = extract common logic;
**Needs manual review** = review before acting (Medium/Low items).

## Functions That Should Not Be Merged

1. **`createColumns` (crop_main_files) vs `createColumns` (create_owid_pages) vs
   `createColumns` (add_lang_categories_to_owid_pages) vs `createColumns` (rename_owid_pages).**
   Despite sharing a name, their columns are materially different (crop: Cropped/Compare/step chain;
   create_owid: New Page/Create Page; add_lang: SVG File/Languages/Categories/Status; rename:
   Old/New title). Merging would destroy page-specific behavior. Action = rename only.

2. **`createUpdatedColumns` (update_owid_charts:85) vs `createUpdatedColumns`
   (collect_templates_data:135).** Same name, completely different domains: OWID _chart_ time/years/
   variable diffs vs OWID _template_ file/year/source/msg. Must remain separate; rename the
   collect one (e.g. `collectTemplateUpdatedColumns`).

3. **`createSkippedColumns` (svglang) vs `createSkippedColumns` (charts).** Not identical — different
   link entity (Commons title vs OWID slug) and different reason field (`reason||error||msg` vs
   `skip_reason`). Parameterize rather than merge verbatim.

4. **`createDownloadedColumns` / `createResultColumns` `#` column.** These intentionally use
   `data: 'template_id'` as the `#` value (stable file id), unlike the 14 functions that use
   `meta.row + 1` (row index). Merging them into the `indexColumn()` meta.row helper would change
   semantics. Keep them as-is (or add a separate `idIndexColumn('template_id')` helper if desired).

5. **`createTableColumns` (fix_nested:62) vs extract/copy.** fix_nested uses a different signature
   `(show_reason, show_result)` and different columns (Oldest File via `renderCommonsFileLinkShort`,
   Result via `row.fix_result?.message`). Not a merge candidate; refactor into shared name/skeleton
   only if desired (Low).

## Proposed Target Structure

Recommended end-state for DataTable column definitions:

-   **`src/static/js/data_table_ajax/macros.js`** (shared, already global):
    -   Keep all existing render helpers (`renderStatus`, `renderWikiLink`, `renderCommonsLink`,
        `renderCommonsFileLink`, `renderCommonsFileLinkShort`, `renderStep`, `diffLink`).
    -   **Add** `renderOwidTitle` (canonical, from the merge) and `indexColumn()`.
-   **New shared module** `src/static/js/data_table_ajax/column_helpers.js` (loaded in
    `base.html` alongside `table.js`/`macros.js`):
    -   `skippedColumns({ linkData, linkRender, reasonData })` — covers svglang & charts skipped tables.
    -   `buildFileTableColumns(middleCols, { show_download, show_nested, err_colmn, show_status })`
        — common `#/File/Status/Download/Error` scaffold for extract & copy.
    -   Optional: `idIndexColumn(dataKey)` for download's `template_id` index variant.
-   **Per-page templates:** keep only thin callers that pass page-specific data keys/renderers to the
    shared helpers; rename the generic `createColumns`/`createTableColumns`/`createUpdatedColumns`
    duplicates to page-specific names for clarity. Page-local render helpers that are genuinely
    unique (`renderCropTemplate`, `renderOwidSlug`, `renderOwidVariableLink`) stay local.

This keeps `initServerTable` as the single wiring point, centralizes shared column _shape_ and
_renderers_, and removes name collisions while preserving behaviorally distinct tables.

## Cleanup Impact

-   **Functions that can be deleted:** the two local copies of `renderOwidTitle`/`renderOwidTemplate`
    (exact duplicate). The inline `#` index block is removed from 14 functions (folded into
    `indexColumn()`).
-   **Functions that can be consolidated:** `createSkippedColumns` ×2 → `skippedColumns({...})`;
    `createTableColumns` (extract/copy) → `buildFileTableColumns(...)`. The 14 wrappers using
    `indexColumn()` shrink by ~4 lines each.
-   **Files affected:**
    -   `src/static/js/data_table_ajax/macros.js` (add `renderOwidTitle`, `indexColumn`)
    -   New `src/static/js/data_table_ajax/column_helpers.js` (add `skippedColumns`,
        `buildFileTableColumns`)
    -   `src/templates/base.html` (add `<script>` for `column_helpers.js`)
    -   11 template detail pages (slim down column functions; rename generic-named ones)
-   **HTML call sites affected:** all 11 `initServerTable(` consumers are touched only indirectly
    (function bodies change); the table-id arguments and call count stay the same. `initServerTable`
    calls themselves do not change.
-   **Estimated reduction in duplicated column-definition logic:** ~17 occurrences of the 4-line `#`
    index block removed (~68 LOC) + 1 exact render-duplicate removed (~6 LOC) + two ~10-line skipped
    builders collapsed to one parameterized helper (~10+ LOC). Net removal of ~85–100 LOC of duplicated
    configuration, plus elimination of 3 sets of colliding names improving maintainability.

## Verification Checklist

-   [ ] Every `initServerTable(` consumer has been accounted for (11 HTML files listed above).
-   [ ] Every column-generation function has been accounted for (16 definition sites inventoried).
-   [ ] Duplicate implementations have been reviewed (`renderOwidTitle`/`renderOwidTemplate`; the `#`
        block; `createSkippedColumns` ×2; `createTableColumns` extract/copy).
-   [ ] Call sites have been identified before removal (per-page `$(document).ready` blocks; no
        `initServerTable` argument changes required).
-   [ ] Behaviorally different functions have not been incorrectly merged (`createColumns` ×4,
        `createUpdatedColumns` ×2, download's `template_id` index, fix_nested).
-   [ ] No unused column-generation functions remain after consolidation (confirm each renamed/thin
        wrapper is still referenced by at least one `initServerTable` call).
-   [ ] Shared helpers added to `macros.js` / `column_helpers.js` load correctly via `base.html`
        before any template that uses them.
-   [ ] Visual/behavioral regression check on each of the 11 job detail pages after refactor (column
        order, visibility flags, and row-index vs template_id `#` values preserved).
