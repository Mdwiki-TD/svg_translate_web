## Objective

Analyze the entire codebase to identify duplicate or overlapping DataTable column-generation functions used by HTML pages that call `initServerTable(`. Produce **only a Markdown audit report** and save it under `docs/reports/`.

## Instructions

1. Recursively scan the repository for all `.html` files containing:

    ```text
    initServerTable(
    ```

2. For every matching HTML file:

    - Record its path.
    - Identify the `initServerTable(...)` invocation(s).
    - Trace the JavaScript configuration passed to the DataTable.
    - Identify every function, helper, callback, or configuration object responsible for creating or defining the DataTable `columns`.

3. Trace those column-generation functions into the JavaScript source files and analyze their implementations.

4. Compare all discovered column-generation implementations for:

    - Exact duplicates.
    - Functions producing the same columns under different names.
    - Functions with only minor differences that could reasonably be consolidated.
    - Shared column definitions that should become reusable helpers/configurations.
    - Functions that are unnecessarily duplicated across modules/pages.
    - Differences that are behaviorally significant and therefore prevent merging.

5. For each duplicate or merge candidate, provide:

    - Function names.
    - Source file paths.
    - HTML pages using them.
    - What columns they create.
    - Why they are considered duplicates or equivalent.
    - Important implementation differences.
    - Recommended canonical function.
    - Whether the other implementation should be merged, renamed, deprecated, or removed.
    - Any call sites that would need to change.

6. Do **not** modify application source code. This task is analysis/reporting only.

7. Do not guess. If a function's behavior cannot be conclusively determined from static analysis, explicitly mark it as **uncertain** and explain why.

8. Rank recommendations by confidence:

    - **High** — clearly duplicate and safe to consolidate.
    - **Medium** — substantially overlapping but requires review.
    - **Low** — potentially related but differences may be intentional.

## Required report structure

The Markdown report must contain:

# DataTable Column Duplication Audit

## Executive Summary

Briefly summarize:

-   Number of matching HTML files.
-   Number of discovered column-generation functions.
-   Number of exact duplicates.
-   Number of likely duplicates.
-   Number of recommended merges.
-   Number of functions recommended for removal.

## HTML Usage Inventory

Create a table:

| HTML File | `initServerTable` Call(s) | Column Function(s) |
| --------- | ------------------------: | ------------------ |

## Column Function Inventory

| Function | File | Used By | Columns Produced | Notes |
| -------- | ---- | ------- | ---------------- | ----- |

## Duplicate / Merge Candidates

For every candidate, provide a subsection containing:

### `<function A>` ↔ `<function B>`

-   **Confidence:** High/Medium/Low
-   **Files:**
-   **HTML consumers:**
-   **Similarity:**
-   **Differences:**
-   **Recommendation:**
-   **Required call-site changes:**
-   **Removal candidate:** Yes/No

Include concise code references where useful, but do not reproduce large source files.

## Recommended Consolidation

Provide a prioritized table:

| Priority | Current Functions | Canonical Function | Action | Confidence |
| -------- | ----------------- | ------------------ | ------ | ---------- |

Clearly distinguish:

-   Merge
-   Remove
-   Keep separate
-   Refactor into shared helper
-   Needs manual review

## Functions That Should Not Be Merged

List functions that initially appear similar but have meaningful behavioral differences.

For each, explain the reason they should remain separate.

## Proposed Target Structure

Describe the recommended end-state architecture for DataTable column definitions, including which functions/configurations should become shared and which should remain page-specific.

## Cleanup Impact

Summarize:

-   Functions that can be deleted.
-   Functions that can be consolidated.
-   Files affected.
-   HTML call sites affected.
-   Estimated reduction in duplicated column-definition logic.

## Verification Checklist

Include a checklist for validating the consolidation after implementation:

-   [ ] Every `initServerTable(` consumer has been accounted for.
-   [ ] Every column-generation function has been accounted for.
-   [ ] Duplicate implementations have been reviewed.
-   [ ] Call sites have been identified before removal.
-   [ ] Behaviorally different functions have not been incorrectly merged.
-   [ ] No unused column-generation functions remain after consolidation.

## Analysis Rules

-   Search the **entire repository**, not only obvious frontend directories.
-   Follow imports/references to locate the actual function definitions.
-   Account for aliases, wrappers, and functions passed indirectly as DataTable configuration.
-   Compare actual column definitions and behavior rather than relying only on function names.
-   Treat ordering, renderers, visibility, sorting, formatting, AJAX-dependent behavior, and conditional columns as meaningful differences.
-   Do not recommend deletion merely because two functions have similar names.
-   Prefer evidence from actual call sites and implementations.
-   Use repository-relative paths and line numbers whenever available.
-   Do not make source-code changes.

## Output Constraint

The **only deliverable is the Markdown report**.

Save it as a suitably named `.md` file inside:

```text
docs/reports/
```

Do not create or modify any other files.
