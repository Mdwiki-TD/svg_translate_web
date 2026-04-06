# Test Classification Report

## Summary Statistics

-   Files to SPLIT: 3

## Detailed Classification Table

| File                                                        | Type  | Action | Tests Count | Destination              |
| ----------------------------------------------------------- | ----- | ------ | ----------- | ------------------------ |
| `tests/main_app/app_routes/auth/test_auth_oauth_helpers.py` | mixed | SPLIT  | 3           | unit(2) + integration(1) |
| `tests/main_app/users/test_current_unit.py`                 | mixed | SPLIT  | 4           | unit(2) + integration(2) |
| `tests/main_app/test_app_factory.py`                        | mixed | SPLIT  | 14          | unit(6) + integration(8) |

## Files Requiring Split

### `tests/main_app/app_routes/auth/test_auth_oauth_helpers.py`

-   **Unit destination**: `tests/unit/app_routes/auth/test_auth_oauth_helpers_unit.py`
    -   Tests: test_complete_login_returns_access_and_identity, test_complete_login_raises_identity_error
-   **Integration destination**: `tests/integration/app_routes/auth/test_auth_oauth_helpers.py`
    -   Tests: test_start_login_returns_redirect_and_request_token

### `tests/main_app/users/test_current_unit.py`

-   **Unit destination**: `tests/unit/services/test_users_service_unit.py`
    -   Tests: test_context_user, test_CurrentUser
-   **Integration destination**: `tests/integration/services/test_users_service.py`
    -   Tests: test_resolve_user_id, test_current_user

### `tests/main_app/test_app_factory.py`

-   **Unit destination**: `tests/unit/test_app_factory_regression_unit.py`
    -   Tests: test_format_stage_timestamp_valid, test_format_stage_timestamp_empty, test_format_stage_timestamp_invalid, test_format_stage_timestamp_afternoon, test_format_stage_timestamp_noon, test_format_stage_timestamp_midnight
-   **Integration destination**: `tests/integration/test_app_factory_regression.py`
    -   Tests: test_create_app_does_not_touch_mysql_when_unconfigured, test_create_app_registers_blueprints, test_create_app_sets_secret_key, test_create_app_configures_cookie_settings, test_create_app_registers_context_processor, test_create_app_registers_error_handlers, test_create_app_strict_slashes_disabled, test_create_app_jinja_env_configured

## Git Commands

# Split files — create new files, then delete old

# Processing tests/main_app/app_routes/auth/test_auth_oauth_helpers.py

cp tests/main_app/app_routes/auth/test_auth_oauth_helpers.py tests/integration/app_routes/auth/test_auth_oauth_helpers.py
cp tests/main_app/app_routes/auth/test_auth_oauth_helpers.py tests/unit/app_routes/auth/test_auth_oauth_helpers_unit.py
git rm tests/main_app/app_routes/auth/test_auth_oauth_helpers.py

# Processing tests/main_app/users/test_current_unit.py

cp tests/main_app/users/test_current_unit.py tests/integration/services/test_users_service.py
cp tests/main_app/users/test_current_unit.py tests/unit/services/test_users_service_unit.py
git rm tests/main_app/users/test_current_unit.py

# Processing tests/main_app/test_app_factory.py

cp tests/main_app/test_app_factory.py tests/integration/test_app_factory_regression.py
cp tests/main_app/test_app_factory.py tests/unit/test_app_factory_regression_unit.py
git rm tests/main_app/test_app_factory.py
