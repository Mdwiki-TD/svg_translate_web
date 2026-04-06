# Supplemental Test Classification Report — Remaining `tests/main_app/` Files

## Summary

| Metric | Count |
|---|---|
| Total files analyzed | 18 |
| MOVE_ONLY → unit | 18 |
| MOVE_ONLY → integration | 0 |
| MOVE_ONLY → functional | 0 |
| Files to SPLIT | 0 |
| Files to DELETE | 0 |

---

## Detailed Classification Table

| File | Type | Action | Tests Count | Destination |
|---|---|---|---|---|
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py` | unit | MOVE_ONLY | 4 | `tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py` |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py` | unit | MOVE_ONLY | 8 | `tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py` |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py` | unit | MOVE_ONLY | 1 | `tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py` |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py` | unit | MOVE_ONLY | 2 | `tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py` |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_inject.py` | unit | MOVE_ONLY | 2 | `tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_inject.py` |
| `tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_upload.py` | unit | MOVE_ONLY | 4 | `tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_upload.py` |
| `tests/main_app/utils/api_services_utils/test_download_file_utils.py` | unit | MOVE_ONLY | 10 | `tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py` |
| `tests/main_app/utils/categories_utils/test_capitalize_category.py` | unit | MOVE_ONLY | 12 | `tests/unit/main_app/utils/categories_utils/test_capitalize_category.py` |
| `tests/main_app/utils/categories_utils/test_categories_utils.py` | unit | MOVE_ONLY | 2 | `tests/unit/main_app/utils/categories_utils/test_categories_utils.py` |
| `tests/main_app/utils/categories_utils/test_extract_categories.py` | unit | MOVE_ONLY | 9 | `tests/unit/main_app/utils/categories_utils/test_extract_categories.py` |
| `tests/main_app/utils/categories_utils/test_find_missing_categories.py` | unit | MOVE_ONLY | 8 | `tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py` |
| `tests/main_app/utils/categories_utils/test_merge_categories.py` | unit | MOVE_ONLY | 7 | `tests/unit/main_app/utils/categories_utils/test_merge_categories.py` |
| `tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py` | unit | MOVE_ONLY | 3 | `tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py` |
| `tests/main_app/utils/wikitext/temps_bot/test_get_titles.py` | unit | MOVE_ONLY | 5 | `tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py` |
| `tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py` | unit | MOVE_ONLY | 10 | `tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py` |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py` | unit | MOVE_ONLY | 13 | `tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py` |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py` | unit | MOVE_ONLY | 9 | `tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py` |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` | unit | MOVE_ONLY | 7 | `tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` |

---

## Classification Rationale

All 18 files use one or more of these isolation patterns:

- **`@patch`** — Mocks external dependencies (mwclient, HTTP calls, wiki API)
- **`mocker.patch`** — Same as above, pytest-mock variant
- **`monkeypatch`** — Replaces module-level objects, settings, paths
- **No real DB/HTTP** — No real MySQL, network calls, or Flask app context

All files test pure functions or single components in isolation. No file exercises full HTTP request/response cycles, real database connections, or multi-component integration flows.

---

## Git Commands

```bash
# ── Move all unit files ──────────────────────────────────────────────────────

# public_jobs_workers/copy_svg_langs/steps
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_inject.py tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_inject.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_upload.py tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_upload.py

# utils/api_services_utils
git mv tests/main_app/utils/api_services_utils/test_download_file_utils.py tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py

# utils/categories_utils
git mv tests/main_app/utils/categories_utils/test_capitalize_category.py tests/unit/main_app/utils/categories_utils/test_capitalize_category.py
git mv tests/main_app/utils/categories_utils/test_categories_utils.py tests/unit/main_app/utils/categories_utils/test_categories_utils.py
git mv tests/main_app/utils/categories_utils/test_extract_categories.py tests/unit/main_app/utils/categories_utils/test_extract_categories.py
git mv tests/main_app/utils/categories_utils/test_find_missing_categories.py tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py
git mv tests/main_app/utils/categories_utils/test_merge_categories.py tests/unit/main_app/utils/categories_utils/test_merge_categories.py

# utils/wikitext/temps_bot
git mv tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py
git mv tests/main_app/utils/wikitext/temps_bot/test_get_titles.py tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py
git mv tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py

# utils/wikitext/titles_utils/last_world_file_utils
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py
```

---

## Full JSON Report

```json
{
  "tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py": {
    "action": "CREATE",
    "source": "tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py",
    "tests": [
      "test_text_task_success",
      "test_text_task_fail",
      "test_extract_text_step_success",
      "test_extract_text_step_fail"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py": {
    "action": "CREATE",
    "source": "tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py",
    "tests": [
      "test_titles_task_success",
      "test_titles_task_manual_title",
      "test_titles_task_limit",
      "test_titles_task_fail",
      "test_extract_titles_step_success",
      "test_extract_titles_step_manual_title",
      "test_extract_titles_step_limit"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py": {
    "action": "CREATE",
    "source": "tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py",
    "tests": ["test_translations_task_stops_on_failure"],
    "type": "unit"
  },
  "tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py": {
    "action": "CREATE",
    "source": "tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_fix_nested.py",
    "tests": [
      "test_fix_nested_task_success",
      "test_fix_nested_task_no_nested"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_inject.py": {
    "action": "CREATE",
    "source": "tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_inject.py",
    "tests": [
      "test_inject_task_success",
      "test_inject_task_no_dir"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/public_jobs_workers/copy_svg_langs/steps/test_upload.py": {
    "action": "CREATE",
    "source": "tests/main_app/public_jobs_workers/copy_svg_langs/steps/test_upload.py",
    "tests": [
      "test_upload_task_disabled",
      "test_upload_task_no_files",
      "test_upload_task_success"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/api_services_utils/test_download_file_utils.py",
    "tests": [
      "test_download_single_file",
      "test_download_multiple_files",
      "test_download_skips_existing_files",
      "test_download_handles_network_error",
      "test_download_handles_404_error",
      "test_download_empty_list",
      "test_download_with_special_characters_in_filename",
      "test_download_with_unicode_filename",
      "test_download_timeout_handling"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/categories_utils/test_capitalize_category.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/categories_utils/test_capitalize_category.py",
    "tests": [
      "test_capitalize_category",
      "test_simple_category",
      "test_category_with_spaces",
      "test_category_with_special_chars",
      "test_single_part_category",
      "test_empty_parts",
      "test_empty_string",
      "test_multiple_colons",
      "test_single_character_parts",
      "test_uppercase_input",
      "test_mixed_case_input",
      "test_numeric_parts",
      "test_unicode_chars"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/categories_utils/test_categories_utils.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/categories_utils/test_categories_utils.py",
    "tests": [
      "test_full_pipeline",
      "test_full_pipeline_2"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/categories_utils/test_extract_categories.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/categories_utils/test_extract_categories.py",
    "tests": [
      "test_extract_categories",
      "test_single_category",
      "test_multiple_categories",
      "test_ignore_non_category_links",
      "test_strip_whitespace",
      "test_no_categories",
      "test_extract_category_with_underscore",
      "test_extract_multiple_special_categories",
      "test_extract_mixed_normal_and_special_categories"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/categories_utils/test_find_missing_categories.py",
    "tests": [
      "test_old_category_not_in_new",
      "test_category_exists_in_both",
      "test_multiple_categories",
      "test_whitespace_ignored",
      "test_empty_old",
      "test_empty_new",
      "test_both_empty",
      "test_old_has_special_new_missing",
      "test_old_has_special_new_present",
      "test_special_chars_case_insensitive_matching",
      "test_multiple_missing_with_underscores"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/categories_utils/test_merge_categories.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/categories_utils/test_merge_categories.py",
    "tests": [
      "test_add_special_category_missing",
      "test_do_not_duplicate_special_category",
      "test_add_multiple_special_categories",
      "test_preserve_special_chars_formatting",
      "test_long_category_name_with_underscores",
      "test_underscore_at_end_of_name",
      "test_add_missing_category",
      "test_do_not_duplicate",
      "test_multiple_categories",
      "test_no_categories_anywhere"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py",
    "tests": [
      "test_get_files_list_prefers_svglanguages",
      "test_get_files_list_falls_back_to_translate",
      "test_get_files_list_no_titles_no_main"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/wikitext/temps_bot/test_get_titles.py",
    "tests": [
      "test_get_titles_from_sample_prompt",
      "test_get_titles_multiple_blocks_and_duplicates",
      "test_get_titles_empty_when_no_entries",
      "test_get_titles_regex_variants"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py",
    "tests": [
      "test_get_titles_from_wikilinks",
      "test_extract_single_file_link",
      "test_extract_multiple_file_links",
      "test_extract_file_link_with_spaces",
      "test_non_file_links_ignored",
      "test_empty_text",
      "test_no_file_links",
      "test_file_link_without_extension_ignored",
      "test_mixed_file_extensions",
      "test_extract_from_owidslidersrcs",
      "test_filter_duplicates",
      "test_no_duplicates_filtering",
      "test_no_owidslidersrcs_template",
      "test_case_insensitive_template_name",
      "test_multiple_owidslidersrcs_templates",
      "test_extract_main_title_and_titles",
      "test_main_title_underscores_to_spaces",
      "test_combined_wikilinks_and_owidslidersrcs"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py",
    "tests": [
      "test_empty_text_returns_empty",
      "test_no_valid_lines_returns_empty",
      "test_single_valid_line",
      "test_multiple_lines_returns_latest_year",
      "test_invalid_filename_skipped",
      "test_invalid_year_format_skipped",
      "test_line_without_exclamation_skipped",
      "test_underscores_replaced_with_spaces",
      "test_filename_with_parentheses",
      "test_filename_with_hyphen",
      "test_multiple_different_years",
      "test_empty_text_returns_none",
      "test_no_template_returns_none",
      "test_template_without_gallery_world_returns_none",
      "test_valid_template_returns_last_world_file",
      "test_case_insensitive_template_name",
      "test_template_with_whitespace_in_name",
      "test_multiple_templates_uses_first",
      "test_template_with_empty_gallery_world"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py",
    "tests": [
      "test_extracts_last_file",
      "test_extracts_last_file_when_unsorted",
      "test_returns_none_when_no_gallery_world",
      "test_returns_none_when_gallery_world_empty"
    ],
    "type": "unit"
  },
  "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py": {
    "action": "CREATE",
    "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py",
    "tests": [
      "test_no_files_returns_empty",
      "test_single_file_returns_it",
      "test_multiple_years_picks_latest",
      "test_unsorted_input_picks_latest",
      "test_year_with_suffixes_picked",
      "test_both_gallery_and_main_title",
      "test_combined_scenario"
    ],
    "type": "unit"
  }
}
```

---

## Updated Cumulative Totals (both reports combined)

| Metric | Count |
|---|---|
| Total files analyzed | 112 + 18 = **130** |
| MOVE_ONLY → unit | **126** |
| MOVE_ONLY → integration | **0** |
| MOVE_ONLY → functional | **0** |
| Files to SPLIT | **0** |
| Files to DELETE | **4** |

All 18 newly analyzed files are unit tests (isolated via mocks/patches), none need splitting, and none are empty stubs.
