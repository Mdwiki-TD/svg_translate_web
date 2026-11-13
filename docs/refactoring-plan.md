# Legacy Function-to-Class Refactoring Plan

## Overview

Refactor standalone functions across the `www/python/src/main_app/` codebase into cohesive, well-layered class-based designs while preserving backward compatibility through thin legacy wrappers.

**Source root:** `www/python/src/main_app/` (referred to as `src/main_app/` below)

---

## Modules to Refactor

### 1. `io/jobs_files_service.py` → `JobFilesService`

**Current state:** 6 standalone functions managing job result files on disk. All share a hidden dependency on `get_jobs_data_dir()` (an `@lru_cache` function reading settings).

**Functions:**
- `get_jobs_data_dir()` → private helper
- `save_data(result_data, filepath)` → private helper
- `save_job_result_by_name(filename, result_data)` → method
- `load_job_result(filename)` → method
- `create_cancel_file(filename)` → method
- `is_cancel_file_exist(filename)` → method

**Callers:**
- `jobs_workers/jobs_worker.py` imports `create_cancel_file`
- `jobs_workers/base_worker.py` imports `save_job_result_by_name`, `is_cancel_file_exist`
- `public/shared_jobs_routes.py` imports `load_job_result`
- `io/__init__.py` re-exports all public functions

**Refactor:**
- New class `JobFilesService` with all 4 public functions as methods.
- Constructor accepts optional `jobs_dir: Path | None = None`; falls back to `get_jobs_data_dir()` lazily.
- Legacy module `io/jobs_files_service.py` keeps all function signatures, delegates to a module-level `_default_service = None` lazy singleton.

**Files changed:**
- `io/jobs_files_service.py` — add `JobFilesService` class + legacy wrappers
- `io/__init__.py` — no change needed (re-exports still work)

---

### 2. `jobs_workers/cancel_registry.py` → `CancelEventRegistry`

**Current state:** 3 functions + 2 module-level globals (`JOBS_CANCEL_EVENTS` dict + `JOBS_CANCEL_EVENTS_LOCK`).

**Functions:**
- `register_cancel_event(job_id, cancel_event)`
- `pop_cancel_event(job_id)`
- `get_cancel_event(job_id)`

**Callers:**
- `jobs_workers/jobs_worker.py` imports `pop_cancel_event`, `get_cancel_event`
- `jobs_workers/backends/thread_backend.py` imports all 3

**Refactor:**
- New class `CancelEventRegistry` encapsulating the dict + lock.
- Constructor creates its own dict/lock (defaults).
- Legacy module keeps all function signatures, delegates to a module-level `_default_registry`.

**Files changed:**
- `jobs_workers/cancel_registry.py` — add `CancelEventRegistry` class + legacy wrappers

---

### 3. `jobs_workers/jobs_worker.py` → `JobStarter` / `JobCanceller`

**Current state:** 9 functions (4 public + 5 private) managing job lifecycle. Mixes job resolution, arg loading, thread running, cancellation, and arg sanitization.

**Public functions:**
- `start_job_form(auth_payload, job_type, args, form_data)` → starts daemon job with form data
- `start_job(auth_payload, job_type, args)` → starts daemon job
- `start_job_cli(auth_payload, job_type, args, app)` → starts job from CLI
- `cancel_job_worker(job_id, job_type, job)` → cancels a running job

**Private functions:**
- `load_job_data(job_type)` → resolves JobData from registries
- `_load_job_args(job_args)` → loads settings into args dict
- `_runner(runner_data, target_class, flask_app)` → thread target
- `_sanitize_args(args)` → removes sensitive keys
- `_start_job_impl(...)` → core start logic

**Callers:**
- `public/shared_jobs_routes.py` imports `cancel_job_worker`, `start_job_form`
- `jobs_workers/cli_jobs.py` imports `start_job_cli`

**Refactor:**
- `JobStarter` class: `start_form()`, `start()`, `start_cli()` methods. Constructor injects `jobs_service` (default `JobsService`), `backend_cls` (default `ThreadBackend`), `cancel_registry` (default `CancelEventRegistry`).
- `JobCanceller` class: `cancel()` method. Constructor injects `cancel_registry`, `jobs_files_service` (default `JobFilesService`), `jobs_service` (default `JobsService`).
- `load_job_data` stays as a module-level pure function (it's a simple dict lookup with no state).
- Legacy wrappers preserve all 4 public function signatures.

**Files changed:**
- `jobs_workers/jobs_worker.py` — add classes + legacy wrappers

---

### 4. `api_services/query_api.py` → `WikiQueryApi`

**Current state:** 8 standalone functions, all taking `site: Site` as parameter. Pure API wrappers around `site.get("query", ...)`.

**Functions:**
- `get_template_pages(title, site, namespace)` → list pages using a template
- `is_pages_exists(titles, site)` → batch existence check
- `resolve_redirects(titles, site)` → resolve redirects
- `search_pages(query, site, namespace, limit)` → search pages
- `get_double_redirects(site)` → find double redirects
- `get_page_links(title, site, namespace)` → get wikilinks on a page
- `get_category_members_titles(site, category_name, namespace)` → paginated category members
- `import_page_from_wiki(site, title, family)` → import from another wiki

**Callers:**
- `api_services/__init__.py` re-exports: `get_page_links`, `get_template_pages`, `is_pages_exists`, `resolve_redirects`, `search_pages`
- `jobs_workers/admin_jobs_workers/crop_main_files/worker.py` imports `is_pages_exists` via `api_services`
- `jobs_workers/admin_jobs_workers/create_owid_pages/worker.py` imports `is_pages_exists` via `api_services`

**Refactor:**
- New class `WikiQueryApi` with constructor accepting `site: Site`.
- All 8 functions become methods (drop the `site` parameter).
- Legacy module keeps all function signatures, creates `WikiQueryApi(site)` per call.

**Files changed:**
- `api_services/query_api.py` — add `WikiQueryApi` class + legacy wrappers
- `api_services/__init__.py` — no change needed (re-exports still work)

---

### 5. `public/routes_service/explorer_utils.py` → `ExplorerDataService`

**Current state:** 7 functions (6 public + 1 private) for reading SVG data files from disk. All share a dependency on `load_svg_data_path()` which reads settings.

**Functions:**
- `load_svg_data_path()` → private config reader
- `_validate_path_under_base(title, sub_dir)` → private path safety check
- `get_main_data(title, filename)` → load JSON data file
- `get_files_full_path(title, sub_dir)` → list all files in subdirectory
- `get_files(title, sub_dir)` → list SVG files in subdirectory
- `get_languages(title, translations_data)` → extract language codes from translations
- `get_informations(title)` → aggregate file/template/language info

**Callers:**
- `public/routes/explorer_routes.py` imports `get_files`, `get_informations`

**Refactor:**
- New class `ExplorerDataService` with constructor accepting optional `svg_data_path: Path | None = None` (falls back to `load_svg_data_path()` lazily) and optional `template_service: TemplateService | None = None`.
- All public functions become methods.
- Legacy wrappers preserve signatures.

**Files changed:**
- `public/routes_service/explorer_utils.py` — add class + legacy wrappers

---

### 6. `public/routes_service/compare.py` → `SvgComparator`

**Current state:** 3 small functions for SVG file comparison.

**Functions:**
- `file_langs(file_path)` → extract languages from SVG
- `analyze_file(file_path)` → analyze one SVG file
- `compare_svg_files(file_path, translated_path)` → compare two SVGs

**Callers:**
- `public/routes/explorer_routes.py` imports `analyze_file`

**Refactor:**
- New class `SvgComparator` with the 3 functions as static/class methods (they are pure — no shared state).
- Legacy wrappers preserve signatures.

**Files changed:**
- `public/routes_service/compare.py` — add class + legacy wrappers

---

### 7. `public/routes_utils.py` → `RequestContextHelper`

**Current state:** 6 functions for request context, auth payload, and job permissions.

**Functions:**
- `_is_admin(user)` → private admin check
- `context_data(wiki_domain, static_server, tool_title)` → template context processor
- `load_auth_payload(user)` → extract auth dict from user object
- `can_run_jobs(user)` → permission check
- `can_run_bg_jobs(user)` → permission check
- `get_job_detail_url(job_id, job_type)` → URL builder

**Callers:**
- `__init__.py` imports `context_data`
- `admin/admin_panel.py` imports `get_job_detail_url`
- `public/shared_jobs_routes.py` imports `can_run_bg_jobs`, `load_auth_payload`
- `public/routes/translate_routes.py` imports `load_auth_payload`

**Refactor:**
- New class `RequestContextHelper` with `context_data()`, `load_auth_payload()`, `can_run_jobs()`, `can_run_bg_jobs()` as methods.
- `get_job_detail_url` stays as a standalone function (it's a pure URL builder with no state).
- Legacy wrappers preserve all signatures.

**Files changed:**
- `public/routes_utils.py` — add class + legacy wrappers

---

### 8. `database/templates_utils.py` → `TemplateDataHelper`

**Current state:** 4 functions for template data manipulation. Pure functions with no I/O.

**Functions:**
- `extract_slug(chart_url)` → extract OWID chart slug from URL
- `match_last_world_year(newest_world_file)` → extract year from filename
- `ensure_template_data(template_data)` → fill missing slug/year, strip File: prefix
- `ensure_template_data_record(record)` → apply ensure_template_data to a TemplateRecord

**Callers:**
- `jobs_workers/admin_jobs_workers/collect_templates_data/worker.py` imports `extract_slug`
- `jobs_workers/admin_jobs_workers/slugs_helpers.py` imports `extract_slug`
- `database/services/charts_and_templates_service.py` imports `extract_slug`
- `database/services/template_service.py` imports `ensure_template_data`

**Refactor:**
- New class `TemplateDataHelper` with all 4 functions as static methods (pure functions, no state).
- Legacy wrappers preserve signatures.

**Files changed:**
- `database/templates_utils.py` — add class + legacy wrappers

---

### 9. `services/copysvg_wrapper/inject_one_file.py` → `SvgInjector`

**Current state:** 5 functions for SVG translation injection. Wraps `SVGTranslationService` from `CopySVGTranslation`.

**Functions:**
- `write_svg_file(output_file, tree)` → write SVG to disk
- `write_msg(stats)` → format injection result message
- `start_svg_injection(inject_file, mapping, overwrite_translations)` → run injection
- `_inject(file_name, data)` → internal injection result handler
- `inject_step_one_file(file, translations, output_file, overwrite_translations)` → full pipeline

**Callers:**
- `services/copysvg_wrapper/__init__.py` re-exports `inject_step_one_file`
- `public/routes/translate_routes.py` imports `inject_step_one_file`
- `public/routes/inject_routes.py` imports `inject_step_one_file`
- `jobs_workers/public_jobs_workers/copy_svg_langs/files_worker.py` imports `inject_step_one_file`

**Refactor:**
- New class `SvgInjector` with constructor accepting optional `config: TranslationConfig | None = None`.
- `inject_step_one_file()` becomes the main public method.
- `write_svg_file`, `write_msg`, `start_svg_injection`, `_inject` become private methods.
- Legacy wrappers preserve all signatures.

**Files changed:**
- `services/copysvg_wrapper/inject_one_file.py` — add class + legacy wrappers
- `services/copysvg_wrapper/__init__.py` — no change needed

---

### 10. `services/copysvg_wrapper/extract_translations.py` → `SvgTranslationExtractor`

**Current state:** 2 functions wrapping `SVGTranslationService.extract`.

**Functions:**
- `_extract_file_translations(source_file)` → private extraction wrapper
- `extract_from_path(main_title_path, fast_return_false)` → main public entry

**Callers:**
- `services/copysvg_wrapper/__init__.py` re-exports `extract_from_path`
- `public/routes/translate_routes.py`, `extract_routes.py`, `inject_routes.py` import it
- `jobs_workers/public_jobs_workers/extract_files_translations/worker.py` imports it
- `jobs_workers/public_jobs_workers/copy_svg_langs/files_worker.py`, `worker.py` import it

**Refactor:**
- New class `SvgTranslationExtractor` with constructor accepting optional `config: TranslationConfig | None = None`.
- `extract_from_path()` becomes the main public method.
- `_extract_file_translations` becomes a private method.
- Legacy wrappers preserve signatures.

**Files changed:**
- `services/copysvg_wrapper/extract_translations.py` — add class + legacy wrappers
- `services/copysvg_wrapper/__init__.py` — no change needed

---

### 11. `jobs_workers/admin_jobs_workers/create_owid_pages/owid_template_converter.py` → `OwidTemplateConverter`

**Current state:** 4 functions for converting OWID template pages to gallery pages. Pure text processing.

**Functions:**
- `create_svglanguages_template(file_name)` → build SVGLanguages wikitext
- `_extract_bullet_url(wikitext, label)` → private URL extraction
- `_extract_display_categories(wikitext)` → private category extraction
- `create_new_text(wikitext, template_title)` → main conversion

**Callers:**
- `create_owid_pages/__init__.py` re-exports `create_new_text`
- `create_owid_pages/worker.py` imports `create_new_text`

**Refactor:**
- New class `OwidTemplateConverter` with all functions as static methods (pure text processing, no state).
- Legacy wrappers preserve signatures.

**Files changed:**
- `create_owid_pages/owid_template_converter.py` — add class + legacy wrappers

---

### 12. `jobs_workers/admin_jobs_workers/crop_main_files/steps/crop_file.py` → `SvgCropper`

**Current state:** 3 functions for SVG cropping via footer removal.

**Functions:**
- `get_max_y_of_element(element)` → calculate max Y boundary
- `remove_footer_and_adjust_height(input_path, cropped_path, footer_id, padding)` → main crop logic
- `crop_svg_file(file_path, cropped_output_path)` → public entry point

**Callers:**
- `crop_main_files/steps/__init__.py` imports `crop_svg_file` (wraps in `CropMainFilesSteps`)
- `crop_main_files/files_processor.py` calls via `CropMainFilesSteps.crop_svg_file`

**Refactor:**
- New class `SvgCropper` with constructor accepting optional `footer_id: str = "footer"` and `padding: float = 10.0`.
- `crop_svg_file()` becomes the main public method.
- `get_max_y_of_element` and `remove_footer_and_adjust_height` become private methods.
- Legacy wrappers preserve signatures.
- Update `CropMainFilesSteps` to delegate to `SvgCropper` instead of the bare function.

**Files changed:**
- `crop_main_files/steps/crop_file.py` — add class + legacy wrappers
- `crop_main_files/steps/__init__.py` — update `CropMainFilesSteps.crop_svg_file` to use `SvgCropper`

---

### 13. `error_pages.py` → `ErrorHandler`

**Current state:** 8 functions + constants for Flask error handling. Mixes request inspection, logging, response building, and Flask registration.

**Functions:**
- `safe_headers(headers)` → redact sensitive headers
- `safe_query()` → redact sensitive query params
- `client_ip()` → extract client IP
- `log_error(label, e, level)` → log + persist error
- `wants_json()` → check if client wants JSON
- `respond(...)` → build error response
- `register_cache_headers(app)` → register no-cache headers
- `register_error_pages(app)` → register all error handlers

**Callers:**
- `__init__.py` imports `register_error_pages`, `register_cache_headers`
- `admin/routes/errors_route.py` imports `get_log_dir` (from logger_config)

**Refactor:**
- New class `ErrorHandler` with constructor accepting optional `error_log_service: ErrorLogService | None = None`.
- `safe_headers`, `safe_query`, `client_ip`, `log_error`, `wants_json`, `respond` become methods.
- `register_cache_headers` and `register_error_pages` stay as standalone functions (they are Flask registration hooks, not business logic).

**Files changed:**
- `error_pages.py` — add `ErrorHandler` class + update `register_error_pages` to use it internally

---

### 14. `logger_config.py` → `LoggingConfigurator`

**Current state:** 7 functions for logging setup. Configuration-oriented with no shared state.

**Functions:**
- `_daily_log_namer(default_name)` → private log file namer
- `_to_level(value, default)` → private level converter
- `prepare_log_file(log_file, project_logger)` → prepare log path
- `setup_file_handler(project_logger, log_file, level, daily_rotation)` → attach file handler
- `setup_logging(level, name, log_file, error_log_file, ...)` → full logging setup
- `get_log_dir()` → get/create log directory
- `configure_logging(level, use_colorlog, name, ...)` → high-level entry point

**Callers:**
- `__init__.py` imports `configure_logging`
- `admin/routes/errors_route.py` imports `get_log_dir`

**Refactor:**
- New class `LoggingConfigurator` encapsulating the full setup pipeline.
- Constructor accepts optional config parameters (level, name, daily_rotation, etc.).
- `configure()` method runs the full setup.
- `get_log_dir()` stays standalone (used independently by error routes).
- Legacy wrappers preserve all signatures.

**Files changed:**
- `logger_config.py` — add `LoggingConfigurator` class + legacy wrappers

---

### 15. `admin/admin_sidebar.py` → `AdminSidebarBuilder`

**Current state:** 4 functions building the admin sidebar menu structure.

**Functions:**
- `dashboard_item(id_, title, icon, endpoint, fallback_href)` → sidebar item factory
- `job_item(job_type, title, icon, disabled)` → sidebar job item factory
- `load_admin_tools()` → build static menu structure (cached)
- `create_admin_sidebar(path, is_admin, list_items)` → generate sidebar HTML

**Callers:**
- `admin/__init__.py` imports `create_admin_sidebar`

**Refactor:**
- New class `AdminSidebarBuilder` with `load_menu()` and `render()` methods.
- `dashboard_item` and `job_item` become private static helper methods.
- Legacy wrappers preserve all signatures.

**Files changed:**
- `admin/admin_sidebar.py` — add class + legacy wrappers

---

## Modules NOT to Refactor (and why)

| Module | Reason to skip |
|---|---|
| `api_services/category.py` | Already has `get_category_members` as a thin wrapper; simple enough |
| `api_services/clients/*` | Already class-based (`WikiSiteClient`, `CommonsSession`, etc.) |
| `api_services/files_service/*` | Already class-based (`FilesService`, `UploadService`) |
| `api_services/mwclient_page/*` | Already class-based (`MwClientPage`) |
| `config/*` | Already class-based (`DbConfig`, `Settings`, etc.) |
| `database/models/*` | SQLAlchemy models — already class-based |
| `database/services/*` | Already class-based service pattern |
| `decorators/*` | Decorators are inherently function-based; no benefit from classes |
| `extensions/*` | Simple Flask extension registration; no business logic |
| `jobs_workers/base_worker.py` | Already class-based (`BaseJobWorker`) |
| `jobs_workers/backends/*` | Already class-based (`JobBackend`, `ThreadBackend`) |
| `jobs_workers/admin_jobs_workers/*/worker.py` | Already class-based workers |
| `public/routes/*` | Flask route handlers — inherently function-based (blueprints/views) |
| `services/auth/*` | Already class-based (`AuthService`, `TokenManager`, `CurrentUserResolver`) |
| `services/copysvg_wrapper/nested_fixer.py` | Already class-based (`NestedStructureService`) |
| `services/core/*` | Already class-based or pure utility |
| `templates_markups/*` | Already class-based (`Sidebar`, `Navbar`) |
| `utils/*` | Pure utility functions; no shared state; classes would add no value |

---

## Implementation Order

Execute in dependency order (leaves first):

1. **`cancel_registry.py`** — no dependencies on other refactored modules
2. **`io/jobs_files_service.py`** — no dependencies on other refactored modules
3. **`database/templates_utils.py`** — pure functions, no dependencies
4. **`public/routes_service/compare.py`** — pure functions, no dependencies
5. **`api_services/query_api.py`** — depends only on mwclient `Site`
6. **`public/routes_service/explorer_utils.py`** — depends on config + TemplateService
7. **`public/routes_utils.py`** — depends on auth resolver
8. **`services/copysvg_wrapper/inject_one_file.py`** — depends on CopySVGTranslation
9. **`services/copysvg_wrapper/extract_translations.py`** — depends on CopySVGTranslation
10. **`jobs_workers/jobs_worker.py`** — depends on #1, #2
11. **`error_pages.py`** — depends on ErrorLogService
12. **`logger_config.py`** — standalone
13. **`admin/admin_sidebar.py`** — depends on templates_markups
14. **`owid_template_converter.py`** — pure text processing
15. **`crop_main_files/steps/crop_file.py`** — standalone SVG processing

---

## Test Strategy

For each module:

1. **Characterization tests** — only if behavior is unclear or untested (most modules already have tests).
2. **Keep existing tests passing** — no modifications to existing test files.
3. **New unit tests** — one test class per new class, testing:
   - Normal case with injected fakes
   - Key edge case (empty input, missing data)
   - Exception handling where relevant
4. **Compatibility check** — verify legacy wrappers return identical results.

Test files to create:
- `tests/unit/io/test_job_files_service.py`
- `tests/unit/jobs_workers/test_cancel_registry.py`
- `tests/unit/jobs_workers/test_job_starter.py`
- `tests/unit/api_services/test_wiki_query_api.py`
- `tests/unit/public/routes_service/test_explorer_data_service.py`
- `tests/unit/public/routes_service/test_svg_comparator.py`
- `tests/unit/public/test_request_context_helper.py`
- `tests/unit/database/test_template_data_helper.py`
- `tests/unit/services/copysvg_wrapper/test_svg_injector.py`
- `tests/unit/services/copysvg_wrapper/test_svg_translation_extractor.py`
- `tests/unit/jobs_workers/test_owid_template_converter.py`
- `tests/unit/jobs_workers/test_svg_cropper.py`
- `tests/unit/test_error_handler.py`
- `tests/unit/test_logging_configurator.py`
- `tests/unit/admin/test_admin_sidebar_builder.py`

---

## Pre-Delivery Checklist

- [ ] All original public functions still exist with identical signatures and defaults
- [ ] Legacy layer contains no duplicated business logic
- [ ] No hidden globals or infrastructure created inside domain logic
- [ ] Every collaborator is an optional `__init__` parameter with a default
- [ ] Solution is as simple as the code allows
- [ ] Tests use pytest, are short, and inject fakes through constructors
- [ ] Existing tests pass unchanged
- [ ] No unrelated changes introduced
- [ ] Comments and docstrings in English
- [ ] Migration guide included per module

---

## Migration Guide (summary)

| Legacy call | New API | Notes |
|---|---|---|
| `save_job_result_by_name(name, data)` | `JobFilesService().save_result(name, data)` | Construct once, reuse |
| `load_job_result(filename)` | `JobFilesService().load_result(filename)` | |
| `register_cancel_event(id, evt)` | `CancelEventRegistry().register(id, evt)` | |
| `start_job_form(auth, type, args, form)` | `JobStarter().start_form(auth, type, args, form)` | |
| `cancel_job_worker(id, type, job)` | `JobCanceller().cancel(id, type, job)` | |
| `get_template_pages(title, site, ns)` | `WikiQueryApi(site).get_template_pages(title, ns)` | Site moved to constructor |
| `is_pages_exists(titles, site)` | `WikiQueryApi(site).is_pages_exists(titles)` | |
| `get_files(title, sub_dir)` | `ExplorerDataService().get_files(title, sub_dir)` | |
| `get_informations(title)` | `ExplorerDataService().get_informations(title)` | |
| `file_langs(path)` | `SvgComparator.file_langs(path)` | Static method |
| `context_data(domain, server, title)` | `RequestContextHelper().context_data(domain, server, title)` | |
| `extract_slug(url)` | `TemplateDataHelper.extract_slug(url)` | Static method |
| `inject_step_one_file(f, t, o, ow)` | `SvgInjector().inject_one_file(f, t, o, ow)` | |
| `extract_from_path(path, fast)` | `SvgTranslationExtractor().extract_from_path(path, fast)` | |
| `create_new_text(wikitext, title)` | `OwidTemplateConverter.create_new_text(wikitext, title)` | Static method |
| `crop_svg_file(path, out)` | `SvgCropper().crop(path, out)` | |
| `log_error(label, exc, level)` | `ErrorHandler().log_error(label, exc, level)` | |
| `setup_logging(...)` | `LoggingConfigurator(...).configure()` | |
| `create_admin_sidebar(path, admin)` | `AdminSidebarBuilder().render(path, admin)` | |
