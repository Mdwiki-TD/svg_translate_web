# DataTable Column-Creation Functions — Duplication & Merge Report

- **Date:** 2025-xx-xx
- **Scope:** All HTML files that call `initServerTable(...)` and the JS functions they use to build column definitions for jQuery DataTables.
- **Files scanned:** 11 `details.html` templates under `src/templates/jobs_templates/` + shared JS in `src/static/js/data_table_ajax/`.
- **Shared helpers already exist:** `src/static/js/data_table_ajax/macros.js` (`renderStatus`, `renderWikiLink`, `renderCommonsFileLink`, `renderCommonsFileLinkShort`, `renderCommonsLink`, `renderStep`, `diffLink`, `statusClass`) and `table.js` (`initServerTable`).

---

## 1. Inventory of column-creation functions

All of these functions are **defined inline inside a `<script>` block in each template** (not in a shared JS module). Every one returns an array of DataTables column objects.

| # | File | Function | # of cols | Column signature (title → data / render) | Used by tables |
|---|------|----------|-----------|------------------------------------------|----------------|
| 1 | `public/extract_files_translations/details.html` | `createTableColumns(show_download, show_nested, err_colmn, show_status)` | 7 | `#`(row#), `File`→renderCommonsFileLink, `Status`→renderStatus(vis), `Download`→steps.download/visible, `Translations`(custom), `Languages`(custom), `Error`(vis) | files_success, files_processed, files_failed |
| 2 | `public/copy_svg_langs/details.html` | `createTableColumns(show_download, show_nested, err_colmn, show_status)` | 10 | `#`(row#), `File`→renderCommonsFileLink, `Status`→renderStatus(vis), `Download`→steps.download(vis), `Nested tags`→steps.nested(vis), `Translations Inserted`(custom), `Translations Updated`(custom), `Inject`→steps.inject, `Upload`→steps.upload, `Error`(vis) | files_success, files_processed, files_skipped, files_failed |
| 3 | `admin/crop_main_files/details.html` | `createColumns()` | 12 | `#`, `Template`→renderCropTemplate, `File`→renderCommonsFileLinkShort, `Cropped`(custom), `Compare`(custom), `Download`, `Crop`, `Upload`, `Update File`, `Update Template`, `Update Page`, `Update Cropped` (all renderStep) | pages_uploaded, pages_updated, files_processed, pages_skipped, pages_failed |
| 4 | `admin/add_svglanguages_template/details.html` | `createProcessedColumns()` | 6 | `#`, `Template`→renderWikiLink(WIKIDOMAIN), `Load Text`→steps.load_template_text, `Generate Text`→steps.generate_template_text, `Add Text`→steps.add_template_text, `Save Page`→steps.save_new_text | pages_processed, pages_success, pages_failed |
| 5 | `admin/add_svglanguages_template/details.html` | `createSkippedColumns()` | 3 | `#`, `Title`→renderCommonsLink, `Reason`(reason\|\|error\|\|msg) | pages_skipped |
| 6 | `admin/update_owid_charts/details.html` | `createUpdatedColumns()` | 7 | `#`, `Slug`→renderOwidSlug, `Min time`, `Max time`, `Years`, `Variable id`, `Source` (all custom, OWID charts) | updated_charts |
| 7 | `admin/update_owid_charts/details.html` | `createFailedColumns()` | 3 | `#`, `Slug`→renderOwidSlug, `Error`(data) | failed_charts |
| 8 | `admin/update_owid_charts/details.html` | `createSkippedColumns()` | 3 | `#`, `Slug`→renderOwidSlug, `Reason`(skip_reason) | skipped_charts |
| 9 | `admin/collect_templates_data/details.html` | `createAddedColumns()` | 2 | `#`, `Title`→renderCommonsLink | pages_added |
| 10 | `admin/collect_templates_data/details.html` | `createUpdatedColumns()` | 10 | `#`, `Title`→renderOwidTitle, `Edit`(custom), `Oldest File`, `Newest File`, `Template year`, `Source`, `Slug`, `Files`, `Msg` (all custom, templates) | pages_updated, pages_skipped, pages_failed |
| 11 | `admin/rename_owid_pages/details.html` | `createColumns(old_title_label, new_title_label)` | 4 | `#`, `old_title`→renderCommonsLink, `new_title`→renderCommonsLink, `Message` | pages_renamed, pages_skipped, pages_redirected, pages_failed |
| 12 | `admin/create_owid_pages/details.html` | `createColumns()` | 7 | `#`, `Template`→renderOwidTemplate, `New Page`(renderWikiLink custom), `Load Text`→steps.load_template_text, `Generate Text`→steps.create_new_text, `Update Page`→steps.update_text, `Create Page`→steps.create_new_page | pages_created, pages_updated, pages_processed, pages_skipped, pages_failed |
| 13 | `admin/download_main_files/details.html` | `createDownloadedColumns()` | 4 | `#`→template_id, `Filename`→renderCommonsFileLink, `View`(custom), `Size` | files_downloaded |
| 14 | `admin/download_main_files/details.html` | `createResultColumns()` | 4 | `#`→template_id, `Template Title`→renderCommonsLink, `Filename`(code), `Reason`(reason\|\|error) | files_skipped, files_failed |
| 15 | `admin/add_lang_categories_to_owid_pages/details.html` | `createColumns()` | 12 | `#`, `OWID Page`→renderCommonsLink, `SVG File`→renderCommonsFileLinkShort, `Languages`(join), `Categories Added`(join), `Load Text`, `Extract SVG`, `Get Langs`, `Build Cats`, `Check Exist`, `Save Page` (renderStep), `Status`→renderStatus | pages_success, pages_skipped, pages_failed |
| 16 | `admin/fix_nested_main_files/details.html` | `createTableColumns(show_reason, show_result)` | 5 | `#`, `Title`→renderCommonsLink, `Oldest File`→renderCommonsFileLinkShort, `Result`(fix_result.message, vis), `Reason`(reason\|\|error\|\|message, vis) | pages_success, pages_failed, pages_skipped |

**Total distinct functions: 16, across 11 files.** None of them live in a shared module today.

---

## 2. Duplicate / redundant patterns (exact or near-identical)

### 2.1 Row-number `#` column — DUPLICATED 10× (the single biggest redundancy)
9 of the 10 functions that have a `#` column re-implement the exact same row-index cell. Two minor textual variants exist but they are functionally identical:

```js
// Variant A (most common)
{ data: null, title: "#", render: function (data, type, row, meta) { return meta.row + 1; } }
// Variant B (arrow form, only in public files #1, #2)
{ data: null, title: "#", render: (data, type, row, meta) => meta.row + 1 }
```

**Where:** files #1–#12 except `download_main_files` (#13/#14 use `data: 'template_id'` instead, which is a real difference — see §5).

**Recommendation:** Extract a single shared helper in `macros.js`:
```js
function indexColumn(title = "#") {
  return { data: null, title, className: "align-middle",
           render: (d, t, r, m) => m.row + 1 };
}
```
Then every function returns `[indexColumn(), ...rest]`.

### 2.2 "Reason / error message" column — DUPLICATED 5× (with 4 different implementations)
This column shows a status message from various fields. It appears, with subtly different fallbacks, in:

| File | Expression |
|------|-----------|
| add_svglanguages_template (#5 `createSkippedColumns`) | `row.reason \|\| row.error \|\| row.msg \|\| '-'` |
| update_owid_charts (#8 `createSkippedColumns`) | `data \|\| '-'` (data = `skip_reason`) |
| download_main_files (#14 `createResultColumns`) | `row.reason \|\| row.error \|\| '-'` |
| fix_nested_main_files (#16 `createTableColumns`) | `row.reason \|\| row.error \|\| row.message \|\| '-'` |
| collect_templates_data (#10 `createUpdatedColumns` "Msg") | `row.msg \|\| row.error \|\| row.reason \|\| ''` |

**Recommendation:** One shared column builder:
```js
function messageColumn(title = "Reason", dataKey = null) {
  return {
    data: dataKey, title, orderable: false,
    render: (data, type, row) =>
      (data || row?.reason || row?.error || row?.msg || row?.message || "-"),
  };
}
```
This collapses all five into a single parametrized column.

### 2.3 "Title" column via `renderCommonsLink` — DUPLICATED 6× (same body, different label/data key)
`render: renderCommonsLink` is used as the column render in 6 places with only the `data` key and `title` differing:

| File | data | title |
|------|------|-------|
| add_svglanguages_template (#5) | `title` | Title |
| collect_templates_data (#9) | `title` | Title |
| rename_owid_pages (#11) | `old_title` / `new_title` | Old/New title |
| download_main_files (#14) | `template_title` | Template Title |
| add_lang_categories (#15) | `page_title` | OWID Page |
| fix_nested_main_files (#16) | `title` | Title |

**Recommendation:** `titleColumn(dataKey, label)` returning `{ data: dataKey, title: label, render: renderCommonsLink }`. (Note: `renderCommonsLink` already ignores the `label` arg, so the label comes from `title`.)

### 2.4 "File" link column — near-duplicate 4× (`renderCommonsFileLink`)
`(title) => renderCommonsFileLink(title)` is repeated in extract (#1), copy (#2), download (#13). (crop #3 and fix_nested #16 use `renderCommonsFileLinkShort` instead — see §4.3.)

**Recommendation:** `fileLinkColumn(dataKey = "title", label = "")`. The `renderCommonsFileLink`/`renderCommonsFileLinkShort` pair is itself redundant (both strip `File:` and differ only in the displayed label) — unify into one with a `label` param (see §4.3).

### 2.5 `renderOwidTemplate` vs `renderOwidTitle` — EXACT DUPLICATE
`admin/create_owid_pages/details.html` and `admin/collect_templates_data/details.html` each define a function with **byte-identical body**:
```js
function renderOwidTemplate(title) {  // ...renderOwidTitle(title) {  (same body)
  if (!title) return '-';
  const display = title.replace(/^Template:OWID\//, '');
  return renderWikiLink(WIKIDOMAIN, title, display);
}
```
**Recommendation:** Delete both; keep one name (e.g. `renderOwidTitle`) in `macros.js`.

---

## 3. Name collisions (same function name, DIFFERENT columns)

These are **not** literal duplicates but are a maintainability hazard — the same identifier means different things in different files:

| Name | Defined in | Actual columns |
|------|-----------|----------------|
| `createColumns()` | crop_main_files | Template + crop/upload steps (12 cols) |
| `createColumns()` | rename_owid_pages | old/new title + message (4 cols) |
| `createColumns()` | create_owid_pages | template + page create steps (7 cols) |
| `createColumns()` | add_lang_categories_to_owid_pages | lang/category steps (12 cols) |
| `createTableColumns(...)` | extract_files_translations | file + translations (7 cols) |
| `createTableColumns(...)` | copy_svg_langs | file + inject/upload (10 cols) |
| `createTableColumns(...)` | fix_nested_main_files | title + result/reason (5 cols) |
| `createUpdatedColumns()` | update_owid_charts | OWID chart times/variable (7 cols) |
| `createUpdatedColumns()` | collect_templates_data | template files/years (10 cols) |
| `createSkippedColumns()` | add_svglanguages_template | Title + Reason (3 cols) |
| `createSkippedColumns()` | update_owid_charts | Slug + Reason (3 cols) |

**Recommendation:** Once columns are moved into a shared module, give each a unique, domain-specific name (or build them from shared column pieces) so the same name never means two different column sets.

---

## 4. Merge opportunities (combine related functions)

### 4.1 `extract` vs `copy` `createTableColumns` — HIGH overlap
Both share an **identical 5-column base**: `#`, `File`(renderCommonsFileLink), `Status`(renderStatus, visible=show_status), `Download`(steps.download, visible=show_download), `Error`(visible=err_colmn). Only the middle "extra" columns differ (extract: Translations + Languages; copy: Nested tags + Translations Inserted/Updated + Inject + Upload).

**Merge plan:** Build a shared `baseFileColumns({show_download, show_status, err_colmn})` returning the 5 common columns, then each template appends its specific columns:
```js
function baseFileColumns({show_download=false, show_status=false, err_colmn=false}) {
  return [
    indexColumn(),
    { data: "title", title: "File", render: renderCommonsFileLink },
    { data: "status", title: "Status", render: renderStatus, visible: show_status },
    { data: "steps.download", title: "Download", orderable:false, render: renderStep, visible: show_download },
    { data: "error", title: "Error", render: undefined, visible: err_colmn },
  ];
}
```
Then `extract` adds Translations/Languages, `copy` adds Nested/Translations Inserted/Updated/Inject/Upload. This removes one full 7-line copy of the base.

### 4.2 `add_svglanguages_template::createProcessedColumns` vs `create_owid_pages::createColumns` — PARTIAL overlap
Both contain a **Template column + "Load Text" + "Generate Text" step columns** that are structurally identical:
- Template column: same idea, but `renderWikiLink(WIKIDOMAIN, title)` (add_svglanguages) vs `renderOwidTemplate` (create_owid_pages). After fixing §2.5, the Template column becomes identical (`renderOwidTitle`).
- `Load Text` → `steps.load_template_text` (identical)
- `Generate Text` → `steps.generate_template_text` (add_svglanguages) vs `steps.create_new_text` (create_owid_pages) — same visual role ("produce new text"), different step key.

**Merge plan:** Extract `templateStepColumns()` returning the Template + Load Text + Generate Text trio (parametrize the generate step key if needed), then each function appends its remaining steps (Save/Add Page vs New Page/Update/Create).

### 4.3 File-link renderers `renderCommonsFileLink` vs `renderCommonsFileLinkShort` — NEAR duplicate
`renderCommonsFileLinkShort(title)` → strips `File:`, label `"File"`.
`renderCommonsFileLink(title, label="")` → strips `File:`, label `File:${striped}` or custom.
These differ only in default label. **Merge into one** `renderCommonsFileLink(title, label)`:
```js
function renderCommonsFileLink(title, label = "File") {
  if (!title) return '-';
  const striped = title.replace('File:', '');
  const display = label === "File" ? "File" : (label || `File:${striped}`);
  return renderWikiLink("commons.wikimedia.org", `File:${striped}`, display);
}
```
(Or simply always use `renderCommonsFileLinkShort` for the `File:` use case and a labeled variant elsewhere.)

### 4.4 Template-title renderers (`renderOwidTemplate`/`renderOwidTitle`/`renderCropTemplate`)
`renderOwidTemplate` and `renderOwidTitle` are identical (see §2.5). `renderCropTemplate` uses a different strip rule (`split('/').slice(1)`), so it stays separate — but if the crop title is always `Template:OWID/...` it could reuse the OWID stripper. Flag for review; not a literal duplicate.

### 4.5 `update_owid_charts` three functions — share a `Slug` column
`createUpdatedColumns`, `createFailedColumns`, `createSkippedColumns` all start with `#` + `Slug`→`renderOwidSlug`. The `#` becomes `indexColumn()` (§2.1) and the `Slug` column becomes `slugColumn()`. Each function then appends only its differing tail (times/source vs error vs reason).

---

## 5. Things that should NOT be merged (real differences)

- **`download_main_files` `#` column** uses `data: 'template_id'` (a real DB id) rather than a rendered row index. Keep as-is or convert deliberately — do not force it into `indexColumn()`.
- **`fix_nested_main_files` "Oldest File"** uses `renderCommonsFileLinkShort` with `data: 'main_file'`; it is genuinely a file column but keyed differently from the File columns in §2.4. Use the unified file-link renderer once §4.3 lands.
- **Charts `createUpdatedColumns`** (times/variable/source) and **templates `createUpdatedColumns`** (files/years/slug) share only the name — their columns are unrelated. They must keep distinct names after extraction.
- **`rename_owid_pages`** columns (old/new title) are unique to that workflow.

---

## 6. Proposed shared column module (`src/static/js/data_table_ajax/columns.js`)

Centralize the reusable pieces so every template calls them instead of re-declaring:

```js
// Reusable column builders (replace inline copies in 11 templates)
function indexColumn(title = "#") { ... }                       // §2.1 (10 dupes)
function titleColumn(dataKey, label) { ... }                    // §2.3 (6 dupes)
function fileLinkColumn(dataKey = "title", label = "File") { ... } // §2.4/§4.3
function messageColumn(title = "Reason", dataKey = null) { ... }  // §2.2 (5 dupes)
function slugColumn() { ... }                                   // §4.5
function templateColumn(dataKey, label) { ... }                 // §2.5/§4.2 (uses renderOwidTitle)
function baseFileColumns(opts) { ... }                          // §4.1
function templateStepColumns(opts) { ... }                      // §4.2
```

And move the duplicated renderers `renderOwidTemplate`/`renderOwidTitle` (keep one) and unify `renderCommonsFileLink`/`renderCommonsFileLinkShort` into `macros.js`.

### Migration impact (files to touch)
| File | Action |
|------|--------|
| `macros.js` | Add `indexColumn`, `titleColumn`, `fileLinkColumn`, `messageColumn`, `slugColumn`, `templateColumn`, `baseFileColumns`, `templateStepColumns`; unify file-link + OWID-title renderers |
| `public/extract_files_translations/details.html` | Replace `createTableColumns` with `baseFileColumns` + extras |
| `public/copy_svg_langs/details.html` | Replace `createTableColumns` with `baseFileColumns` + extras |
| `admin/crop_main_files/details.html` | `createColumns` → use `indexColumn` + shared renderers |
| `admin/add_svglanguages_template/details.html` | `createProcessedColumns`/`createSkippedColumns` → shared builders |
| `admin/update_owid_charts/details.html` | 3 funcs → `indexColumn` + `slugColumn` + `messageColumn` |
| `admin/collect_templates_data/details.html` | 2 funcs → shared builders; drop `renderOwidTitle` |
| `admin/rename_owid_pages/details.html` | `createColumns` → `indexColumn` + `titleColumn` |
| `admin/create_owid_pages/details.html` | `createColumns` → shared template builders; drop `renderOwidTemplate` |
| `admin/download_main_files/details.html` | 2 funcs → `titleColumn`/`messageColumn` (keep template_id `#`) |
| `admin/add_lang_categories_to_owid_pages/details.html` | `createColumns` → `indexColumn` + `titleColumn` + shared file/step cols |
| `admin/fix_nested_main_files/details.html` | `createTableColumns` → `indexColumn` + `titleColumn` + `fileLinkColumn` + `messageColumn` |

---

## 7. Summary of what to remove / merge

| Category | Count | Action |
|----------|-------|--------|
| Row-`#` index column bodies | 10 | → 1 shared `indexColumn()` |
| Reason/error message column bodies | 5 | → 1 shared `messageColumn()` |
| Title column via `renderCommonsLink` | 6 | → 1 shared `titleColumn()` |
| File link column bodies | 4 | → 1 shared `fileLinkColumn()` |
| `renderOwidTemplate` ≡ `renderOwidTitle` | 2 | → 1 function |
| `renderCommonsFileLink` / `renderCommonsFileLinkShort` | 2 | → 1 unified renderer |
| `extract` vs `copy` `createTableColumns` base | 2 | → shared `baseFileColumns()` |
| `createProcessedColumns` vs `create_owid_pages::createColumns` | 2 | → shared `templateStepColumns()` + `templateColumn()` |
| Name collisions (`createColumns`, `createTableColumns`, `createUpdatedColumns`, `createSkippedColumns`) | 11 definitions | Rename to unique domain names after extraction |

**Net result:** ~30 nearly-identical inline column blocks collapse to ~8 reusable builders in one shared module, eliminating copy-paste drift (e.g., the `meta.row + 1` is currently written two different ways) and making future column changes one-edit instead of eleven.
