# Test Classification Report — Batch 1 (admins, api_services, core)

---

## 1. `tests/main_app/admins/test_admins_required.py`

**Test functions:**
| Function | Classification |
|---|---|
| `test_admin_required_redirects_when_not_logged_in` | Unit |
| `test_admin_required_blocks_non_admin` | Unit |
| `test_admin_required_allows_admin` | Unit |
| `test_admin_required_not_logged_in` | Unit |
| `test_admin_required_not_admin` | Unit |
| `test_admin_required_is_admin` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/app_routes/admin/test_admins_required.py`

---

## 2. `tests/main_app/api_services/clients/test_commons_client.py`

**Test functions:**
| Function | Classification |
|---|---|
| `TestCreateCommonsSession::test_creates_session` | Unit |
| `TestCreateCommonsSession::test_default_user_agent` | Unit |
| `TestCreateCommonsSession::test_custom_user_agent` | Unit |
| `TestDownloadCommonsFileCore::test_successful_download` | Unit |
| `TestDownloadCommonsFileCore::test_spaces_converted_to_underscores` | Unit |
| `TestDownloadCommonsFileCore::test_custom_timeout` | Unit |
| `TestDownloadCommonsFileCore::test_http_error_raises_exception` | Unit |
| `TestDownloadCommonsFileCore::test_network_error_raises_exception` | Unit |
| `TestDownloadCommonsFileCore::test_timeout_error_raises_exception` | Unit |
| `TestDownloadCommonsFileCore::test_filename_is_url_encoded` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/clients/test_commons_client.py` (already mirrors src structure)

---

## 3. `tests/main_app/api_services/clients/test_wiki_client.py`

**Test functions:**
| Function | Classification |
|---|---|
| `test_build_upload_site_uses_decrypted_tokens_and_consumer` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/clients/test_wiki_client.py` (already mirrors src structure)

---

## 4. `tests/main_app/api_services/mwclient_page/test_mwclient_page.py`

**Test functions:**
| Function | Classification |
|---|---|
| `TestLoadPage::test_returns_page_on_success` | Unit |
| `TestLoadPage::test_caches_page_on_second_call` | Unit |
| `TestLoadPage::test_invalid_page_title` | Unit |
| `TestLoadPage::test_generic_exception` | Unit |
| `TestCheckExists::test_page_exists` | Unit |
| `TestCheckExists::test_page_does_not_exist` | Unit |
| `TestCheckExists::test_load_page_fails` | Unit |
| `TestEditPageInternal::test_success` | Unit |
| `TestEditPageInternal::test_assert_user_failed` | Unit |
| `TestEditPageInternal::test_user_blocked` | Unit |
| `TestEditPage::test_load_page_fails_invalid_title` | Unit |
| `TestEditPage::test_load_page_fails_generic` | Unit |
| `TestEditPageRateLimit::test_ratelimited` | Unit |
| `TestEditPageRateLimit::test_ratelimited_then_success` | Unit |
| `TestEditPageRateLimit::test_ratelimited_exhausts_all_retries` | Unit |
| `TestEditPageRateLimit::test_ratelimited_then_other_api_error` | Unit |
| `TestEditPageRateLimit::test_edit_error_no_retry` | Unit |
| `TestEditPageRateLimit::test_retry_sleep_delays_are_correct` | Unit |
| `TestEditWithRetry::test_succeeds_on_first_retry` | Unit |
| `TestEditWithRetry::test_returns_ratelimited_after_all_retries` | Unit |
| `TestEditWithRetry::test_stops_early_on_non_ratelimited_error` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/mwclient_page/test_mwclient_page.py` (already mirrors src structure)

---

## 5. `tests/main_app/api_services/mwclient_page/test_mwclient_page2.py`

**Test functions:**
| Function | Classification |
|---|---|
| `TestEditPageErrors::test_edit_error` | Unit |
| `TestEditPageErrors::test_api_error_other` | Unit |
| `TestEditPageErrors::test_generic_exception` | Unit |
| `TestEditPageErrors::test_unexpected_exception` | Unit |
| `TestEditPageProtectedErrors::test_protected_page_error` | Unit |
| `TestEditPageProtectedErrors::test_protected_page_no_retry` | Unit |
| `TestEditPageProtectedErrors::test_ratelimited_then_protected` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/mwclient_page/test_mwclient_page2.py` (already mirrors src structure)

---

## 6. `tests/main_app/api_services/test_category.py`

**Test functions:**
| Function | Classification |
|---|---|
| `test_get_category_members_api_success` | Unit |
| `test_get_category_members_api_no_results` | Unit |
| `test_get_category_members_api_request_exception` | Unit |
| `test_get_category_members_api_timeout` | Unit |
| `test_get_category_members_api_http_error` | Unit |
| `test_get_category_members_api_multiple_pages` | Unit |
| `test_get_category_members_filters_templates` | Unit |
| `test_get_category_members_custom_category` | Unit |
| `test_get_category_members_empty_results` | Unit |
| `test_get_category_members_no_valid_templates` | Unit |
| `test_get_category_members_case_sensitivity` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/test_category.py` (already mirrors src structure)

---

## 7. `tests/main_app/api_services/test_pages_api.py`

**Test functions:**
| Function | Classification |
|---|---|
| `TestIsPageExists::test_page_exists_returns_true` | Unit |
| `TestIsPageExists::test_page_not_exists_returns_false` | Unit |
| `TestIsPageExists::test_page_exists_logs_info` | Unit |
| `TestIsPageExists::test_page_not_exists_logs_warning` | Unit |
| `TestCreatePage::test_create_page_success` | Unit |
| `TestCreatePage::test_create_page_without_summary` | Unit |
| `TestCreatePage::test_create_page_missing_page_name` | Unit |
| `TestCreatePage::test_create_page_missing_wikitext` | Unit |
| `TestCreatePage::test_create_page_missing_site` | Unit |
| `TestCreatePage::test_create_page_load_page_exception` | Unit |
| `TestCreatePage::test_create_page_edit_exception` | Unit |
| `TestUpdateFileText::test_valid_inputs` | Unit |
| `TestUpdateFileText::test_adds_file_prefix` | Unit |
| `TestUpdateFileText::test_missing_original_file_returns_error` | Unit |
| `TestUpdateFileText::test_missing_updated_file_text_returns_error` | Unit |
| `TestUpdateFileText::test_missing_site_returns_error` | Unit |
| `TestUpdateFileText::test_empty_original_file_returns_error` | Unit |
| `TestUpdateFileText::test_empty_updated_file_text_returns_error` | Unit |
| `TestUpdateFileText::test_multiple_missing_fields_returns_error` | Unit |
| `TestUpdateFileText::test_with_prefixed_original_file` | Unit |
| `TestUpdateFileText::test_error_message_format` | Unit |
| `TestUpdatePageText::test_valid_inputs_calls_edit` | Unit |
| `TestUpdatePageText::test_missing_page_name_returns_error` | Unit |
| `TestUpdatePageText::test_missing_updated_text_returns_error` | Unit |
| `TestUpdatePageText::test_missing_site_returns_error` | Unit |
| `TestUpdatePageText::test_edit_exception_returns_error` | Unit |
| `TestUpdatePageText::test_default_empty_summary` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/test_pages_api.py` (already mirrors src structure)

---

## 8. `tests/main_app/api_services/test_text_api.py`

**Test functions:**
| Function | Classification |
|---|---|
| `TestGetFileText::test_valid_inputs_returns_text` | Unit |
| `TestGetFileText::test_adds_file_prefix` | Unit |
| `TestGetFileText::test_missing_file_name_returns_empty_string` | Unit |
| `TestGetFileText::test_missing_site_returns_empty_string` | Unit |
| `TestGetFileText::test_empty_file_name_returns_empty_string` | Unit |
| `TestGetFileText::test_both_missing_returns_empty_string` | Unit |
| `TestGetFileText::test_with_prefixed_filename` | Unit |
| `TestGetFileText::test_site_exception_returns_empty_string` | Unit |
| `TestGetFileText::test_text_method_exception_returns_empty_string` | Unit |
| `TestGetPageText::test_valid_inputs_returns_text` | Unit |
| `TestGetPageText::test_does_not_add_file_prefix` | Unit |
| `TestGetPageText::test_missing_page_name_returns_empty_string` | Unit |
| `TestGetPageText::test_missing_site_returns_empty_string` | Unit |
| `TestGetPageText::test_site_exception_returns_empty_string` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/test_text_api.py` (already mirrors src structure)

---

## 9. `tests/main_app/api_services/test_text_bot.py`

**Test functions:**
| Function | Classification |
|---|---|
| `test_get_wikitext_success` | Unit |
| `test_get_wikitext_not_found` | Unit |
| `test_get_wikitext_error` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/test_text_bot.py` (already mirrors src structure)

---

## 10. `tests/main_app/api_services/test_upload_bot.py`

**Test functions:**
| Function | Classification |
|---|---|
| `test_upload_file_no_site` | Unit |
| `test_upload_file_not_found_on_commons` | Unit |
| `test_upload_file_not_found_on_server` | Unit |
| `test_upload_file_success` | Unit |
| `test_upload_file_fileexists_no_change` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/test_upload_bot.py` (already mirrors src structure)

---

## 11. `tests/main_app/api_services/test_upload_bot_new.py`

**Test functions:**
| Function | Classification |
|---|---|
| `TestFixFileName::test_strips_file_prefix_lowercase` | Unit |
| `TestFixFileName::test_strips_file_prefix_uppercase` | Unit |
| `TestFixFileName::test_strips_file_prefix_mixed_case` | Unit |
| `TestFixFileName::test_strips_surrounding_whitespace` | Unit |
| `TestFixFileName::test_no_prefix_unchanged` | Unit |
| `TestFixFileName::test_none_file_name_not_processed` | Unit |
| `TestCheckKwargs::test_no_site` | Unit |
| `TestCheckKwargs::test_no_file_name` | Unit |
| `TestCheckKwargs::test_no_file_path` | Unit |
| `TestCheckKwargs::test_existing_file_mode_file_not_on_commons` | Unit |
| `TestCheckKwargs::test_new_file_mode_file_already_on_commons` | Unit |
| `TestCheckKwargs::test_file_not_on_server` | Unit |
| `TestCheckKwargs::test_all_valid_existing_file` | Unit |
| `TestCheckKwargs::test_all_valid_new_file` | Unit |
| `TestUploadFileInternal::test_success` | Unit |
| `TestUploadFileInternal::test_assert_user_failed` | Unit |
| `TestUploadFileInternal::test_user_blocked` | Unit |
| `TestUploadFileInternal::test_insufficient_permission` | Unit |
| `TestUploadFileInternal::test_file_exists` | Unit |
| `TestUploadFileInternal::test_maximum_retries_exceeded` | Unit |
| `TestUploadFileInternal::test_timeout` | Unit |
| `TestUploadFileInternal::test_connection_error` | Unit |
| `TestUploadFileInternal::test_http_error` | Unit |
| `TestUploadFileInternal::test_rate_limited` | Unit |
| `TestUploadFileInternal::test_fileexists_no_change` | Unit |
| `TestUploadFileInternal::test_other_api_error` | Unit |
| `TestUploadFileInternal::test_unexpected_exception` | Unit |
| `TestUploadWithRetry::test_succeeds_on_first_retry` | Unit |
| `TestUploadWithRetry::test_exhausts_all_retries` | Unit |
| `TestUploadWithRetry::test_sleeps_correct_delays` | Unit |
| `TestUploadWithRetry::test_stops_early_on_non_ratelimited_error` | Unit |
| `TestUploadWithRetry::test_succeeds_on_second_retry` | Unit |
| `TestUpload::test_success` | Unit |
| `TestUpload::test_check_kwargs_fails_early` | Unit |
| `TestUpload::test_rate_limited_then_success` | Unit |
| `TestUpload::test_rate_limited_exhausts_all_retries` | Unit |
| `TestUpload::test_rate_limited_sleeps_correct_delays` | Unit |
| `TestUpload::test_non_ratelimited_error_no_retry` | Unit |
| `TestUpload::test_new_file_upload_success` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/api_services/test_upload_bot_new.py` (already mirrors src structure)

---

## 12. `tests/main_app/core/test_crypto.py`

**Test functions:**
| Function | Classification |
|---|---|
| `test_encrypt_decrypt_roundtrip` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/core/test_crypto.py` (already mirrors src structure)

---

## Summary

| File                                   | All Tests | Action    | Destination                                |
| -------------------------------------- | --------- | --------- | ------------------------------------------ |
| `admins/test_admins_required.py`       | 6 Unit    | MOVE_ONLY | `app_routes/admin/test_admins_required.py` |
| `clients/test_commons_client.py`       | 10 Unit   | MOVE_ONLY | (already correct)                          |
| `clients/test_wiki_client.py`          | 1 Unit    | MOVE_ONLY | (already correct)                          |
| `mwclient_page/test_mwclient_page.py`  | 21 Unit   | MOVE_ONLY | (already correct)                          |
| `mwclient_page/test_mwclient_page2.py` | 7 Unit    | MOVE_ONLY | (already correct)                          |
| `test_category.py`                     | 11 Unit   | MOVE_ONLY | (already correct)                          |
| `test_pages_api.py`                    | 27 Unit   | MOVE_ONLY | (already correct)                          |
| `test_text_api.py`                     | 14 Unit   | MOVE_ONLY | (already correct)                          |
| `test_text_bot.py`                     | 3 Unit    | MOVE_ONLY | (already correct)                          |
| `test_upload_bot.py`                   | 5 Unit    | MOVE_ONLY | (already correct)                          |
| `test_upload_bot_new.py`               | 39 Unit   | MOVE_ONLY | (already correct)                          |
| `test_crypto.py`                       | 1 Unit    | MOVE_ONLY | (already correct)                          |

**Total: 145 tests, all Unit, all MOVE_ONLY.** No SPLIT or DELETE actions needed. Every file uses mocks/patches/MagicMagic with no real Flask app context or real DB — textbook unit tests. The only file whose destination path differs from its current path is `test_admins_required.py`, which should move from `admins/` to `app_routes/admin/` to mirror the source module location.

# Test Classification Report — Batch 2 (app_routes)

---

## 1. `tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py`

| Test Function                                               | Classification |
| ----------------------------------------------------------- | -------------- |
| `test_add_coordinator_catches_both_lookup_and_value_errors` | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py`
-   **Rationale:** Tests a single internal function `_add_coordinator` with monkeypatched Flask globals (request, flash, redirect, url_for). No Flask app context, no real DB. Pure unit test.

---

## 2. `tests/main_app/app_routes/admin/test_sidebar.py`

| Test Function                                          | Classification |
| ------------------------------------------------------ | -------------- |
| `test_generate_list_item`                              | **Unit**       |
| `test_create_side_marks_active_item`                   | **Unit**       |
| `test_generate_list_item_basic`                        | **Unit**       |
| `test_generate_list_item_with_icon`                    | **Unit**       |
| `test_generate_list_item_with_target`                  | **Unit**       |
| `test_generate_list_item_with_icon_and_target`         | **Unit**       |
| `test_create_side_no_active_item`                      | **Unit**       |
| `test_create_side_with_active_item`                    | **Unit**       |
| `test_sidebar_contains_jobs_section`                   | **Unit**       |
| `test_sidebar_contains_collect_main_files_job_link`    | **Unit**       |
| `test_sidebar_contains_fix_nested_main_files_job_link` | **Unit**       |
| `test_sidebar_marks_collect_main_files_as_active`      | **Unit**       |
| `test_sidebar_marks_fix_nested_main_files_as_active`   | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/admin/test_sidebar.py`
-   **Rationale:** All tests call pure helper functions (`generate_list_item`, `create_side`) from the sidebar module directly. No Flask app context, no mocks needed, no DB. Pure unit tests.

---

## 3. `tests/main_app/app_routes/auth/test_auth_cookie.py`

| Test Function                                | Classification |
| -------------------------------------------- | -------------- |
| `test_sign_and_extract_roundtrip`            | **Unit**       |
| `test_extract_user_id_tampered_returns_none` | **Unit**       |
| `test_state_token_roundtrip`                 | **Unit**       |
| `test_state_token_invalid_returns_none`      | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/auth/test_auth_cookie.py`
-   **Rationale:** Tests cookie signing/verification functions directly. Uses real serializers but no Flask app context or DB. Pure unit tests.

---

## 4. `tests/main_app/app_routes/auth/test_auth_oauth_helpers.py`

| Test Function                                         | Classification |
| ----------------------------------------------------- | -------------- |
| `test_start_login_returns_redirect_and_request_token` | **Unit**       |
| `test_complete_login_returns_access_and_identity`     | **Unit**       |
| `test_complete_login_raises_identity_error`           | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/auth/test_auth_oauth_helpers.py`
-   **Rationale:** Uses stubbed `mwoauth` classes and monkeypatching. One test uses `app.test_request_context("/")` but this is a minimal request context, not a full Flask test client flow. All external dependencies are stubbed. Unit tests.

---

## 5. `tests/main_app/app_routes/auth/test_cookie.py`

| Test Function                             | Classification |
| ----------------------------------------- | -------------- |
| `test_sign_user_id`                       | **Unit**       |
| `test_extract_user_id_valid_token`        | **Unit**       |
| `test_extract_user_id_invalid_token`      | **Unit**       |
| `test_sign_state_token`                   | **Unit**       |
| `test_verify_state_token_success`         | **Unit**       |
| `test_verify_state_token_invalid_payload` | **Unit**       |
| `test_verify_state_token_bad_signature`   | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/auth/test_cookie.py`
-   **Rationale:** Tests cookie module functions with monkeypatched settings and real `URLSafeTimedSerializer`. No Flask app context, no DB. Pure unit tests. (Note: overlaps with `test_auth_cookie.py` — potential DUPLICATE candidate, but not DELETE per classification scope.)

---

## 6. `tests/main_app/app_routes/auth/test_oauth.py`

| Test Function                        | Classification |
| ------------------------------------ | -------------- |
| `test_get_handshaker`                | **Unit**       |
| `test_get_handshaker_without_config` | **Unit**       |
| `test_start_login`                   | **Unit**       |
| `test_complete_login`                | **Unit**       |
| `test_complete_login_identity_error` | **Unit**       |
| `test_oauthidentityerror`            | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/auth/test_oauth.py`
-   **Rationale:** All tests use monkeypatched `mwoauth`, `url_for`, and `get_handshaker`. No Flask test client, no real network, no DB. Pure unit tests.

---

## 7. `tests/main_app/app_routes/auth/test_rate_limit.py`

| Test Function                                | Classification |
| -------------------------------------------- | -------------- |
| `test_ratelimiter_enforces_limit`            | **Unit**       |
| `test_ratelimiter_tracks_keys_independently` | **Unit**       |
| `test_rate_limiter_allow_and_try_after`      | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/auth/test_rate_limit.py`
-   **Rationale:** Tests the `RateLimiter` class in isolation. Pure in-memory data structure tests. No Flask, no DB, no mocks needed. Pure unit tests.

---

## 8. `tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py`

| Test Function                                   | Classification |
| ----------------------------------------------- | -------------- |
| `test_user_token_record_has_username_attribute` | **Unit**       |
| `test_username_access_in_f_string`              | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py`
-   **Rationale:** Tests dataclass attribute access and f-string formatting. No Flask context, no DB, no mocks. Trivial unit tests.

---

## 9. `tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py`

| Test Function                                  | Classification |
| ---------------------------------------------- | -------------- |
| `test_get_commons_file_url_basic`              | **Unit**       |
| `test_get_commons_file_url_with_spaces`        | **Unit**       |
| `test_get_commons_file_url_with_special_chars` | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py`
-   **Rationale:** Tests a single pure URL-building function `_get_commons_file_url`. No Flask context, no mocks, no DB. Pure unit tests.

---

## 10. `tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py`

| Test Function                            | Classification |
| ---------------------------------------- | -------------- |
| `test_download_svg_file_success`         | **Unit**       |
| `test_detect_nested_tags`                | **Unit**       |
| `test_fix_nested_tags`                   | **Unit**       |
| `test_verify_fix`                        | **Unit**       |
| `test_upload_fixed_svg_success`          | **Unit**       |
| `test_process_fix_nested_success`        | **Unit**       |
| `test_download_svg_file_failure`         | **Unit**       |
| `test_detect_nested_tags_empty`          | **Unit**       |
| `test_fix_nested_tags_returns_false`     | **Unit**       |
| `test_verify_fix_all_fixed`              | **Unit**       |
| `test_upload_fixed_svg_no_user`          | **Unit**       |
| `test_upload_fixed_svg_no_site`          | **Unit**       |
| `test_upload_fixed_svg_upload_failure`   | **Unit**       |
| `test_process_fix_nested_download_fails` | **Unit**       |
| `test_process_fix_nested_no_nested_tags` | **Unit**       |
| `test_process_fix_nested_fix_fails`      | **Unit**       |
| `test_process_fix_nested_no_tags_fixed`  | **Unit**       |
| `test_process_fix_nested_upload_fails`   | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py`
-   **Rationale:** All 18 tests use `@patch` to mock external dependencies (`download_one_file`, `match_nested_tags`, `fix_nested_file`, `get_user_site`, `upload_file`). Tests individual worker functions and the `process_fix_nested` orchestrator in isolation. No Flask app context, no real DB, no test client. Pure unit tests.

---

## 11. `tests/main_app/app_routes/utils/test_args_utils.py`

| Test Function                                             | Classification |
| --------------------------------------------------------- | -------------- |
| `test_parse_args_upload_disabled_by_config`               | **Unit**       |
| `test_parse_args_manual_main_title_and_limits`            | **Unit**       |
| `test_parse_args_empty_manual_main_title`                 | **Unit**       |
| `test_parse_args_upload_enabled_when_not_disabled`        | **Unit**       |
| `test_parse_args_upload_disabled_explicit_zero`           | **Unit**       |
| `test_parse_args_upload_not_in_form`                      | **Unit**       |
| `test_parse_args_manual_main_title_file_prefix_lowercase` | **Unit**       |
| `test_parse_args_manual_main_title_only_file_colon`       | **Unit**       |
| `test_parse_args_manual_main_title_whitespace_only`       | **Unit**       |
| `test_parse_args_overwrite_not_present`                   | **Unit**       |
| `test_parse_args_default_titles_limit`                    | **Unit**       |
| `test_parse_args_custom_titles_limit`                     | **Unit**       |
| `test_parse_args_disable_uploads_other_string`            | **Unit**       |
| `test_parse_args_ignore_existing_task_not_set`            | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/utils/test_args_utils.py`
-   **Rationale:** Tests `parse_args` function with `MultiDict` form data. Pure function testing with no Flask context, no DB. Unit tests.

---

## 12. `tests/main_app/app_routes/utils/test_compare.py`

| Test Function                         | Classification |
| ------------------------------------- | -------------- |
| `test_file_langs_extracts_languages`  | **Unit**       |
| `test_analyze_file_reports_languages` | **Unit**       |
| `test_compare_svg_files_returns_both` | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/utils/test_compare.py`
-   **Rationale:** Tests SVG language extraction and comparison functions using real file I/O on `tmp_path`. No Flask context, no DB, no mocks. These test interaction between file I/O and parsing logic — borderline unit/integration, but since they test a single module's pure functions with temp files, they are **Unit** tests.

---

## 13. `tests/main_app/app_routes/utils/test_explorer_utils.py`

| Test Function                                | Classification |
| -------------------------------------------- | -------------- |
| `test_get_main_data_reads_json`              | **Unit**       |
| `test_get_files_full_path_returns_all_files` | **Unit**       |
| `test_get_files_filters_svg`                 | **Unit**       |
| `test_get_languages_extracts_codes`          | **Unit**       |
| `test_get_informations_compiles_summary`     | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/utils/test_explorer_utils.py`
-   **Rationale:** Tests explorer utility functions with monkeypatched paths and real file I/O via `tmp_path`. Tests interaction between file system and JSON parsing within a single module. No Flask context, no DB, no test client. **Unit** tests (with real filesystem fixtures).

---

## 14. `tests/main_app/app_routes/utils/test_fix_nested_utils.py`

| Test Function                                 | Classification |
| --------------------------------------------- | -------------- |
| `test_create_task_folder`                     | **Unit**       |
| `test_save_metadata`                          | **Unit**       |
| `test_log_to_task`                            | **Unit**       |
| `test_create_task_folder_idempotent`          | **Unit**       |
| `test_create_task_folder_with_string_path`    | **Unit**       |
| `test_create_task_folder_creates_nested_dirs` | **Unit**       |
| `test_log_to_task_appends_multiple_messages`  | **Unit**       |
| `test_log_to_task_includes_timestamp`         | **Unit**       |
| `test_save_metadata_with_non_string_values`   | **Unit**       |
| `test_save_metadata_overwrites_existing`      | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/utils/test_fix_nested_utils.py`
-   **Rationale:** Tests utility functions for task folder creation, metadata saving, and logging. Uses real file I/O via `tmp_path` but no Flask context, no DB, no mocks. Pure unit tests.

---

## 15. `tests/main_app/app_routes/utils/test_routes_utils_unit.py`

| Test Function                              | Classification |
| ------------------------------------------ | -------------- |
| `test_get_error_message_known_and_unknown` | **Unit**       |
| `test_format_timestamp_variants`           | **Unit**       |
| `test_order_stages_and_format_task`        | **Unit**       |
| `test_load_auth_payload_happy_path`        | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/utils/test_routes_utils_unit.py`
-   **Rationale:** Tests pure helper functions (`get_error_message`, `_format_timestamp`, `order_stages`, `format_task`, `load_auth_payload`). No Flask context, no DB, no mocks. Pure unit tests.

---

## 16. `tests/main_app/app_routes/utils/test_thumbnail_utils.py`

| Test Function                    | Classification |
| -------------------------------- | -------------- |
| `test_save_thumb_returns_false2` | **Unit**       |

-   **Action:** MOVE_ONLY
-   **Destination:** `tests/main_app/app_routes/utils/test_thumbnail_utils.py`
-   **Rationale:** Tests a single function `save_thumb` with temp files. No Flask context, no DB, no mocks. Pure unit test.

---

## Summary Table

| File                                                         | Tests | Classification | Action    | Destination                                     |
| ------------------------------------------------------------ | ----- | -------------- | --------- | ----------------------------------------------- |
| `admin/admin_routes/test_coordinators_exception_handling.py` | 1     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/admin/admin_routes/` |
| `admin/test_sidebar.py`                                      | 13    | Unit           | MOVE_ONLY | `tests/main_app/app_routes/admin/`              |
| `auth/test_auth_cookie.py`                                   | 4     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/auth/`               |
| `auth/test_auth_oauth_helpers.py`                            | 3     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/auth/`               |
| `auth/test_cookie.py`                                        | 7     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/auth/`               |
| `auth/test_oauth.py`                                         | 6     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/auth/`               |
| `auth/test_rate_limit.py`                                    | 3     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/auth/`               |
| `fix_nested/test_explorer_routes_undo.py`                    | 2     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/fix_nested/`         |
| `fix_nested/test_fix_nested_routes_unit.py`                  | 3     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/fix_nested/`         |
| `fix_nested/test_fix_nested_worker.py`                       | 18    | Unit           | MOVE_ONLY | `tests/main_app/app_routes/fix_nested/`         |
| `utils/test_args_utils.py`                                   | 14    | Unit           | MOVE_ONLY | `tests/main_app/app_routes/utils/`              |
| `utils/test_compare.py`                                      | 3     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/utils/`              |
| `utils/test_explorer_utils.py`                               | 5     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/utils/`              |
| `utils/test_fix_nested_utils.py`                             | 10    | Unit           | MOVE_ONLY | `tests/main_app/app_routes/utils/`              |
| `utils/test_routes_utils_unit.py`                            | 4     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/utils/`              |
| `utils/test_thumbnail_utils.py`                              | 1     | Unit           | MOVE_ONLY | `tests/main_app/app_routes/utils/`              |

**Total: 97 tests across 16 files. All classified as Unit tests. All require MOVE_ONLY action.**

**Note:** `test_auth_cookie.py` and `test_cookie.py` test the same cookie module with overlapping functionality — consider consolidating or deleting one as a follow-up, but not classified as DELETE here since both contain unique test cases.

# Test Classification Report — Batch 3 (db)

---

## 1. `tests/main_app/db/test_db_class.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `test_Database_init_basic` | Unit |
| `test_Database_connect` (skipped) | Unit |
| `test_Database_ensure_connection_new` | Unit |
| `test_Database_ensure_connection_ping` | Unit |
| `test_Database_close` | Unit |
| `test_Database_context_manager` | Unit |
| `test_Database_execute_query_success` | Unit |
| `test_Database_fetch_query_success` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_db_class.py`

All tests mock `pymysql` and test the `Database` class in isolation.

---

## 2. `tests/main_app/db/test_db_CoordinatorsDB.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `test_CoordinatorRecord` | Unit |
| `test_ensure_table` | Unit |
| `test_fetch_by_id_success` | Unit |
| `test_fetch_by_id_not_found` | Unit |
| `test_fetch_by_username_success` | Unit |
| `test_fetch_by_username_not_found` | Unit |
| `test_seed` | Unit |
| `test_list` | Unit |
| `test_add_success` | Unit |
| `test_add_empty_username` | Unit |
| `test_add_duplicate` | Unit |
| `test_set_active` | Unit |
| `test_delete` | Unit |
| `test_seed_empty_list` | Unit |
| `test_seed_only_whitespace` | Unit |
| `test_seed_strips_whitespace` | Unit |
| `test_row_to_record_with_all_fields` | Unit |
| `test_row_to_record_is_active_falsy` | Unit |
| `test_add_with_whitespace_trimmed` | Unit |
| `test_set_active_deactivate` | Unit |
| `test_set_active_not_found` | Unit |
| `test_delete_not_found` | Unit |
| `test_list_empty` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_db_CoordinatorsDB.py`

All tests mock the `Database` class via `mocker.patch`. No Flask app context, no real DB.

---

## 3. `tests/main_app/db/test_db_Jobs.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `test_JobRecord` | Unit |
| `test_ensure_table` | Unit |
| `test_create_success` | Unit |
| `test_create_failure` | Unit |
| `test_get_success` | Unit |
| `test_get_not_found` | Unit |
| `test_list_all` | Unit |
| `test_list_filtered` | Unit |
| `test_delete_success` | Unit |
| `test_delete_exception` | Unit |
| `test_update_status_running` | Unit |
| `test_update_status_completed` | Unit |
| `test_update_status_generic` | Unit |
| `test_update_status_not_found` | Unit |
| `test_update_status_with_result_file_on_running` | Unit |
| `test_update_status_failed` | Unit |
| `test_update_status_cancelled` | Unit |
| `test_list_with_limit` | Unit |
| `test_row_to_record_with_all_fields` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_db_Jobs.py`

All tests mock the `Database` class. Pure unit tests.

---

## 4. `tests/main_app/db/test_db_OwidCharts.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `TestOwidChartRecord::test_basic_creation` | Unit |
| `TestOwidChartRecord::test_template_source_auto_generated` | Unit |
| `TestOwidChartRecord::test_optional_fields_default_none` | Unit |
| `TestOwidChartsDB::test_init_creates_table` | Unit |
| `TestOwidChartsDB::test_fetch_by_id_success` | Unit |
| `TestOwidChartsDB::test_fetch_by_id_not_found` | Unit |
| `TestOwidChartsDB::test_fetch_by_slug_success` | Unit |
| `TestOwidChartsDB::test_fetch_by_slug_not_found` | Unit |
| `TestOwidChartsDB::test_list_returns_all_charts` | Unit |
| `TestOwidChartsDB::test_list_published_filters_published` | Unit |
| `TestOwidChartsDB::test_add_success` | Unit |
| `TestOwidChartsDB::test_add_missing_slug_raises_value_error` | Unit |
| `TestOwidChartsDB::test_add_missing_title_raises_value_error` | Unit |
| `TestOwidChartsDB::test_add_duplicate_slug_raises_value_error` | Unit |
| `TestOwidChartsDB::test_update_success` | Unit |
| `TestOwidChartsDB::test_update_nonexistent_raises_lookup_error` | Unit |
| `TestOwidChartsDB::test_delete_success` | Unit |
| `TestOwidChartsDB::test_delete_nonexistent_raises_lookup_error` | Unit |
| `TestOwidChartsDB::test_update_chart_data_partial_update` | Unit |
| `TestOwidChartsDB::test_update_chart_data_boolean_fields` | Unit |
| `TestOwidChartsDB::test_row_to_record_converts_booleans` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_db_OwidCharts.py`

All tests use `@patch("src.main_app.db.db_OwidCharts.Database")`. Pure unit tests.

---

## 5. `tests/main_app/db/test_db_Settings.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `test_settings_db_init` | Unit |
| `test_get_all_parses_boolean_true` | Unit |
| `test_get_all_parses_boolean_false` | Unit |
| `test_get_all_parses_integer` | Unit |
| `test_get_all_parses_integer_invalid` | Unit |
| `test_get_all_parses_json` | Unit |
| `test_get_all_parses_json_invalid` | Unit |
| `test_get_all_parses_string` | Unit |
| `test_get_all_handles_none` | Unit |
| `test_get_raw_all` | Unit |
| `test_get_by_key_found` | Unit |
| `test_get_by_key_not_found` | Unit |
| `test_create_setting_success` | Unit |
| `test_create_setting_failure` | Unit |
| `test_create_setting_serialize_boolean` | Unit |
| `test_create_setting_serialize_integer` | Unit |
| `test_create_setting_serialize_json` | Unit |
| `test_update_setting_success` | Unit |
| `test_update_setting_not_found` | Unit |
| `test_update_setting_failure` | Unit |
| `test_update_setting_preserves_type` | Unit |
| `test_update_setting_with_value_type_skips_select` | Unit |
| `test_update_setting_without_value_type_queries_db` | Unit |
| `test_update_setting_with_value_type_serializes_correctly` | Unit |
| `test_serialize_value_none` | Unit |
| `test_serialize_value_boolean` | Unit |
| `test_serialize_value_integer` | Unit |
| `test_serialize_value_json` | Unit |
| `test_serialize_value_string` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_db_Settings.py`

All tests use `@patch("src.main_app.db.db_Settings.Database")`. Pure unit tests.

---

## 6. `tests/main_app/db/test_db_Templates.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `test_TemplateRecord` | Unit |
| `test_ensure_table` | Unit |
| `test_fetch_by_id_success` | Unit |
| `test_fetch_by_id_not_found` | Unit |
| `test_fetch_by_title_success` | Unit |
| `test_list` | Unit |
| `test_add_success` | Unit |
| `test_add_duplicate` | Unit |
| `test_add_empty_title` | Unit |
| `test_update_success` | Unit |
| `test_delete_success` | Unit |
| `test_row_to_record_with_all_fields` | Unit |
| `test_row_to_record_with_none_main_file` | Unit |
| `test_fetch_by_title_not_found` | Unit |
| `test_add_with_whitespace` | Unit |
| `test_update_not_found` | Unit |
| `test_delete_not_found` | Unit |
| `test_list_empty` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_db_Templates.py`

All tests mock the `Database` class via `mocker.patch`. Pure unit tests.

---

## 7. `tests/main_app/db/test_exceptions.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `test_MaxUserConnectionsError` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_exceptions.py`

Tests a single custom exception class in isolation. No mocks needed.

---

## 8. `tests/main_app/db/test_fix_nested_task_store.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `test_init_schema` | Unit |
| `test_create_task_success` | Unit |
| `test_create_task_failure` | Unit |
| `test_get_task_success` | Unit |
| `test_get_task_json_error` | Unit |
| `test_get_task_not_found` | Unit |
| `test_update_status` | Unit |
| `test_update_nested_counts` | Unit |
| `test_update_download_result` | Unit |
| `test_update_upload_result` | Unit |
| `test_update_error` | Unit |
| `test_list_tasks` | Unit |
| `test_list_tasks_failure` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_fix_nested_task_store.py`

All tests mock the `Database` class via `mocker.patch`. Pure unit tests.

---

## 9. `tests/main_app/db/test_svg_db.py`

**Test Functions:**
| Function | Classification |
|---|---|
| `test_get_db` | Unit |
| `test_close_cached_db` | Unit |
| `test_execute_query` | Unit |
| `test_fetch_query` | Unit |
| `test_execute_query_safe` | Unit |
| `test_fetch_query_safe` | Unit |

**Action:** `MOVE_ONLY`
**Destination:** `tests/main_app/db/unit/test_svg_db.py`

All tests mock `Database` and `settings`. The `cleanup_cached_db` fixture resets module-level state but no real DB is used.

---

## Summary Table

| File                            | Tests | Classification | Action    | Destination                                            |
| ------------------------------- | ----- | -------------- | --------- | ------------------------------------------------------ |
| `test_db_class.py`              | 8     | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_db_class.py`              |
| `test_db_CoordinatorsDB.py`     | 22    | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_db_CoordinatorsDB.py`     |
| `test_db_Jobs.py`               | 19    | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_db_Jobs.py`               |
| `test_db_OwidCharts.py`         | 21    | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_db_OwidCharts.py`         |
| `test_db_Settings.py`           | 29    | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_db_Settings.py`           |
| `test_db_Templates.py`          | 18    | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_db_Templates.py`          |
| `test_exceptions.py`            | 1     | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_exceptions.py`            |
| `test_fix_nested_task_store.py` | 13    | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_fix_nested_task_store.py` |
| `test_svg_db.py`                | 6     | Unit           | MOVE_ONLY | `tests/main_app/db/unit/test_svg_db.py`                |

**Total: 137 tests, all Unit, all MOVE_ONLY.** No SPLIT or DELETE actions needed. Every file in this batch uses mocks/patches exclusively, never touches a real database or Flask app context, and tests single classes/functions in isolation.

---

## Test Classification Report - Batch 4 (jobs_workers)

---

### 1. `tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py`

**Test functions (17):**

-   `TestTemplateInfo.test_template_info_initialization` → **Unit**
-   `TestTemplateInfo.test_template_info_steps_initialized` → **Unit**
-   `TestTemplateInfo.test_template_info_to_dict` → **Unit**
-   `TestAddSvgSVGLanguagesTemplateInit.test_worker_initialization` → **Unit**
-   `TestAddSvgSVGLanguagesTemplateInit.test_get_job_type` → **Unit**
-   `TestAddSvgSVGLanguagesTemplateInit.test_get_initial_result` → **Unit**
-   `TestLoadTemplates.test_load_templates_filters_owid_templates` → **Unit**
-   `TestLoadTemplates.test_apply_limits_with_no_limit` → **Unit**
-   `TestLoadTemplates.test_apply_limits_applies_limit` → **Unit**
-   `TestProcessTemplate.test_process_template_success_flow` → **Unit**
-   `TestProcessTemplate.test_process_template_load_step_fails` → **Unit**
-   `TestProcessTemplate.test_process_template_generate_step_fails` → **Unit**
-   `TestStepLoadTemplateText.test_load_template_text_success` → **Unit**
-   `TestStepLoadTemplateText.test_load_template_text_returns_empty_string` → **Unit**
-   `TestStepLoadTemplateText.test_load_template_text_skips_if_already_has_svglanguages` → **Unit**
-   `TestStepGenerateTemplateText.test_generate_template_text_success` → **Unit**
-   `TestStepGenerateTemplateText.test_generate_template_text_no_translate_link` → **Unit**
-   `TestStepAddTemplate.test_add_template_success` → **Unit**
-   `TestStepAddTemplate.test_add_template_skips_if_identical` → **Unit**
-   `TestStepSaveNewText.test_save_new_text_success` → **Unit**
-   `TestStepSaveNewText.test_save_new_text_failure` → **Unit**
-   `TestHelperMethods.test_fail_marks_step_and_file_as_failed` → **Unit**
-   `TestHelperMethods.test_skip_step_marks_step_as_skipped` → **Unit**
-   `TestHelperMethods.test_append_adds_template_to_result` → **Unit**
-   `TestProcessMethod.test_process_success` → **Unit**
-   `TestProcessMethod.test_process_fails_without_site` → **Unit**
-   `TestProcessMethod.test_process_handles_cancellation` → **Unit**
-   `TestAddSvgSVGLanguagesTemplateToTemplates.test_function_creates_and_runs_worker` → **Unit**

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py`

---

### 2. `tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py`

**Test functions (22):** All tests use `mock_services` fixture with heavy monkeypatching of all external services. Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py`

---

### 3. `tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py`

**Test functions (1):**

-   `test_create_new_text` → **Unit** (pure function test, no mocks needed, no Flask/DB)

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py`

---

### 4. `tests/main_app/jobs_workers/crop_main_files/test_crop_file.py`

**Test functions (17):** All test pure SVG manipulation functions using `tmp_path` fixtures and `ET.parse`. No Flask, no DB, no mocks of external services (except one patch for exception testing).

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/crop_main_files/test_crop_file.py`

---

### 5. `tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py`

**Test functions (20):** All test `crop_main_files_for_templates` function with `mock_services` fixture monkeypatching `base_worker.jobs_service`. Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py`

---

### 6. `tests/main_app/jobs_workers/crop_main_files/test_download.py`

**Test functions (7):** All test `download_file_for_cropping` with mocked `download_one_file`. Unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/crop_main_files/test_download.py`

---

### 7. `tests/main_app/jobs_workers/crop_main_files/test_process_new.py`

**Test functions (29):** All tests use `mock_services` fixture with extensive monkeypatching of every external dependency (jobs_service, template_service, API clients, crop functions, etc.). Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/crop_main_files/test_process_new.py`

---

### 8. `tests/main_app/jobs_workers/crop_main_files/test_upload.py`

**Test functions (17):** All test `upload_cropped_file` with mocked `upload_file`. Pure unit tests using `tmp_path`.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/crop_main_files/test_upload.py`

---

### 9. `tests/main_app/jobs_workers/test_base_worker.py`

**Test functions (15):** Tests `job_exception_handler` decorator and `BaseJobWorker` class using a `ConcreteTestWorker` subclass. All use `mock_base_services` fixture. Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/test_base_worker.py`

---

### 10. `tests/main_app/jobs_workers/test_collect_main_files_worker.py`

**Test functions (20):** All test `collect_main_files_for_templates` with `mock_services` fixture monkeypatching template_service, jobs_service, get_category_members, get_wikitext, etc. Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/test_collect_main_files_worker.py`

---

### 11. `tests/main_app/jobs_workers/test_download_main_files_worker.py`

**Test functions (27):** Tests `download_file_from_commons`, `download_main_files_for_templates`, `generate_main_files_zip`, `create_main_files_zip`. All use mocked `requests.Session` and `mock_services`. Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/test_download_main_files_worker.py`

---

### 12. `tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py`

**Test functions (12):** Tests `fix_nested_main_files_for_templates` and `repair_nested_svg_tags` with mocked dependencies. Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py`

---

### 13. `tests/main_app/jobs_workers/test_jobs_worker.py`

**Test functions (9):** Tests job dispatcher functions (`start_job`, `cancel_job`, `_runner`) with mocked `create_job` and `Thread`. Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/test_jobs_worker.py`

---

### 14. `tests/main_app/jobs_workers/test_worker_cancellation.py`

**Test functions (3):**

-   `test_collect_main_files_worker_cancellation` → **Unit**
-   `test_fix_nested_main_files_worker_cancellation` → **Unit**
-   `test_worker_handles_deleted_job` → **Unit**

All use `mock_common_services` fixture. Pure unit tests.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/test_worker_cancellation.py`

---

### 15. `tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py`

**Test functions (17):** Tests pure utility functions (`load_link_file_name`, `add_template_to_text`) and regex patterns (`RE_SVG_LANG`, `RE_TRANSLATE`). No mocks, no DB, no Flask.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py`

---

### 16. `tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py`

**Test functions (9):** Tests `generate_cropped_filename` pure function. No mocks, no DB, no Flask.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py`

---

### 17. `tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py`

**Test functions (6):** Tests `generate_result_file_name` pure function. No mocks, no DB, no Flask.

**Action:** MOVE_ONLY
**Destination:** `tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py`

---

## Summary

| File                                       | Type | Action    | Destination                               |
| ------------------------------------------ | ---- | --------- | ----------------------------------------- |
| `test_add_svglanguages_template_worker.py` | Unit | MOVE_ONLY | `jobs_workers/add_svglanguages_template/` |
| `test_create_owid_pages_worker.py`         | Unit | MOVE_ONLY | `jobs_workers/create_owid_pages/`         |
| `test_owid_template_converter.py`          | Unit | MOVE_ONLY | `jobs_workers/create_owid_pages/`         |
| `test_crop_file.py`                        | Unit | MOVE_ONLY | `jobs_workers/crop_main_files/`           |
| `test_crop_main_files_worker.py`           | Unit | MOVE_ONLY | `jobs_workers/crop_main_files/`           |
| `test_download.py`                         | Unit | MOVE_ONLY | `jobs_workers/crop_main_files/`           |
| `test_process_new.py`                      | Unit | MOVE_ONLY | `jobs_workers/crop_main_files/`           |
| `test_upload.py`                           | Unit | MOVE_ONLY | `jobs_workers/crop_main_files/`           |
| `test_base_worker.py`                      | Unit | MOVE_ONLY | `jobs_workers/`                           |
| `test_collect_main_files_worker.py`        | Unit | MOVE_ONLY | `jobs_workers/`                           |
| `test_download_main_files_worker.py`       | Unit | MOVE_ONLY | `jobs_workers/`                           |
| `test_fix_nested_main_files_worker.py`     | Unit | MOVE_ONLY | `jobs_workers/`                           |
| `test_jobs_worker.py`                      | Unit | MOVE_ONLY | `jobs_workers/`                           |
| `test_worker_cancellation.py`              | Unit | MOVE_ONLY | `jobs_workers/`                           |
| `test_add_svglanguages_template_utils.py`  | Unit | MOVE_ONLY | `jobs_workers/utils/`                     |
| `test_crop_main_files_utils.py`            | Unit | MOVE_ONLY | `jobs_workers/utils/`                     |
| `test_jobs_workers_utils.py`               | Unit | MOVE_ONLY | `jobs_workers/utils/`                     |

**Totals:** 17 files → 17 MOVE_ONLY, 0 SPLIT, 0 DELETE. All 17 files are **Unit tests** — every file uses mocks/patches, no Flask test client, no real DB, no end-to-end flows.
