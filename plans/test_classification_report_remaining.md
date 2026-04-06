# Supplemental Test Classification Report — Remaining `tests/main_app/` Files

## Summary

| Metric               | Count |
| -------------------- | ----- |
| Total files analyzed | 18    |
| MOVE_ONLY → unit     | 18    |

---

## Detailed Classification Table

| File                                                                                                  | Type | Action    | Tests Count | Destination                                                                                       |
| ----------------------------------------------------------------------------------------------------- | ---- | --------- | ----------- | ------------------------------------------------------------------------------------------------- |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py`                        | unit | MOVE_ONLY | 4           | `tests/unit/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py`                        |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py`                      | unit | MOVE_ONLY | 8           | `tests/unit/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py`                      |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py`                | unit | MOVE_ONLY | 1           | `tests/unit/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py`                |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py`                          | unit | MOVE_ONLY | 2           | `tests/unit/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py`                          |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_inject.py`                              | unit | MOVE_ONLY | 2           | `tests/unit/public_jobs_workers/copy_svg_langs/steps/test_inject.py`                              |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_upload.py`                              | unit | MOVE_ONLY | 4           | `tests/unit/public_jobs_workers/copy_svg_langs/steps/test_upload.py`                              |
| `tests/main_app/utils/api_services_utils/test_download_file_utils.py`                                 | unit | MOVE_ONLY | 10          | `tests/unit/utils/api_services_utils/test_download_file_utils.py`                                 |
| `tests/main_app/utils/categories_utils/test_capitalize_category.py`                                   | unit | MOVE_ONLY | 12          | `tests/unit/utils/categories_utils/test_capitalize_category.py`                                   |
| `tests/main_app/utils/categories_utils/test_categories_utils.py`                                      | unit | MOVE_ONLY | 2           | `tests/unit/utils/categories_utils/test_categories_utils.py`                                      |
| `tests/main_app/utils/categories_utils/test_extract_categories.py`                                    | unit | MOVE_ONLY | 9           | `tests/unit/utils/categories_utils/test_extract_categories.py`                                    |
| `tests/main_app/utils/categories_utils/test_find_missing_categories.py`                               | unit | MOVE_ONLY | 8           | `tests/unit/utils/categories_utils/test_find_missing_categories.py`                               |
| `tests/main_app/utils/categories_utils/test_merge_categories.py`                                      | unit | MOVE_ONLY | 7           | `tests/unit/utils/categories_utils/test_merge_categories.py`                                      |
| `tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py`                                      | unit | MOVE_ONLY | 3           | `tests/unit/utils/wikitext/temps_bot/test_get_files_list.py`                                      |
| `tests/main_app/utils/wikitext/temps_bot/test_get_titles.py`                                          | unit | MOVE_ONLY | 5           | `tests/unit/utils/wikitext/temps_bot/test_get_titles.py`                                          |
| `tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py`                                           | unit | MOVE_ONLY | 10          | `tests/unit/utils/wikitext/temps_bot/test_temps_bot.py`                                           |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py`            | unit | MOVE_ONLY | 13          | `tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py`            |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py`           | unit | MOVE_ONLY | 9           | `tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py`           |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` | unit | MOVE_ONLY | 7           | `tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` |

---

## Classification Rationale

All 18 files use one or more of these isolation patterns:

-   **`@patch`** — Mocks external dependencies (mwclient, HTTP calls, wiki API)
-   **`mocker.patch`** — Same as above, pytest-mock variant
-   **`monkeypatch`** — Replaces module-level objects, settings, paths
-   **No real DB/HTTP** — No real MySQL, network calls, or Flask app context

All files test pure functions or single components in isolation. No file exercises full HTTP request/response cycles, real database connections, or multi-component integration flows.

---

## Git Commands

```bash
# ── Move all unit files ──────────────────────────────────────────────────────

# public_jobs_workers/copy_svg_langs/steps
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py tests/unit/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py tests/unit/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py tests/unit/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py tests/unit/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_inject.py tests/unit/public_jobs_workers/copy_svg_langs/steps/test_inject.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_upload.py tests/unit/public_jobs_workers/copy_svg_langs/steps/test_upload.py

# utils/api_services_utils
git mv tests/main_app/utils/api_services_utils/test_download_file_utils.py tests/unit/utils/api_services_utils/test_download_file_utils.py

# utils/categories_utils
git mv tests/main_app/utils/categories_utils/test_capitalize_category.py tests/unit/utils/categories_utils/test_capitalize_category.py
git mv tests/main_app/utils/categories_utils/test_categories_utils.py tests/unit/utils/categories_utils/test_categories_utils.py
git mv tests/main_app/utils/categories_utils/test_extract_categories.py tests/unit/utils/categories_utils/test_extract_categories.py
git mv tests/main_app/utils/categories_utils/test_find_missing_categories.py tests/unit/utils/categories_utils/test_find_missing_categories.py
git mv tests/main_app/utils/categories_utils/test_merge_categories.py tests/unit/utils/categories_utils/test_merge_categories.py

# utils/wikitext/temps_bot
git mv tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py tests/unit/utils/wikitext/temps_bot/test_get_files_list.py
git mv tests/main_app/utils/wikitext/temps_bot/test_get_titles.py tests/unit/utils/wikitext/temps_bot/test_get_titles.py
git mv tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py tests/unit/utils/wikitext/temps_bot/test_temps_bot.py

# utils/wikitext/titles_utils/last_world_file_utils
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py
```
