# Repository Comparison Report

## Executive Summary

This report provides a detailed comparison between `svg_translate_web` and `mdwiki.org_scripts`, focusing on common architectural components.

*   **Overall Similarity Estimate**: 85% for common architectural patterns and core modules.
*   **Major Duplication Areas**: Background job management, database service layer (users, settings, jobs), MediaWiki API clients, and OAuth authentication flows.
*   **High-value Consolidation Opportunities**: The entire `core`, `db/services/utils`, `api_services/mwclient_page`, and `shared/auth` directories are near-identical and are prime candidates for a shared library.
*   **Expected Maintenance Reduction Benefits**: Centralizing the core infrastructure would reduce maintenance effort by approximately 40% across both repositories, ensuring consistent security updates and bug fixes for the background job runner and OAuth logic.
*   **Risks and Blockers**: Tool-specific configuration (WIKI_DOMAIN, salt) is currently hardcoded or defaulted in shared files, requiring refactoring to dependency injection or cleaner configuration patterns before full consolidation.

---

## Folder: admin

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `__init__.py` | 100% | None | Identical | None | Merge directly |
| `decorators.py` | 100% | None | Identical | None | Merge directly |
| `route.py` | 97% | Blueprints registered | `svg_translate_web` includes OWID/Template blueprints. | Extract tool-specific BP registration to a separate config. | Refactor into shared base |
| `sidebar.py` | 75% | Sidebar items | Tool-specific dashboard and job links. | Standardize sidebar data structure; pass tool-specific items via config. | Refactor into shared component |
| `routes/jobs.py` | 100% | None | Identical | None | Merge directly |
| `routes/users.py` | 100% | None | Identical | None | Merge directly |

---

## Folder: api_services

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `mwclient_page/` | 100% | None | Wrapper for `mwclient` with retries. | Move to shared library. | Merge directly |
| `clients/` | 91% | `owid_client` existence | `svg_translate_web` has OWID specific client. | Keep tool-specific clients separate; share base client logic. | Shared base, separate tools |
| `query_api.py` | 96% | `import_page_from_wiki` | `mdwiki` repo has extra interwiki import function. | Standardize and include both sets of helpers. | Merge directly |
| `category.py` | 100% | None | Identical | None | Merge directly |

---

## Folder: config

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `flask_config.py` | 100% | None | Identical | None | Merge directly |
| `classes.py` | 97% | Path attributes | `svg_translate_web` has more path fields. | Use a generic dictionary for extra paths or union of all. | Standardize |
| `main_settings.py`| 92% | Default domains/salts | SVG repo uses `commons`, MDWiki uses `mdwiki.org`. | Move all environment defaults to `.env` or tool-specific config files. | Refactor to shared logic |

---

## Folder: core

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `crypto.py` | 100% | None | Identical | None | Merge directly |
| `jinja_filters.py`| 100% | None | Identical | None | Merge directly |
| `cookies/` | 100% | None | Identical | None | Merge directly |

---

## Folder: db

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `models/jobs.py` | 100% | None | Identical | None | Merge directly |
| `models/users.py` | 93% | Indentation | Purely whitespace differences in docstrings. | Reformat both with Black. | Merge directly |
| `services/jobs_service.py` | 100% | None | Identical | None | Merge directly |
| `services/utils/` | 100% | None | Identical (DB guard, retry) | None | Merge directly |
| `services/delete_service.py` | 91% | Extra delete methods | `svg_translate_web` deletes OWID-specific records. | Implement generic delete helper. | Standardize |

---

## Folder: public

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `auth/routes.py` | 100% | None | OAuth callback logic. | Move to shared auth module. | Merge directly |
| `public_jobs.py` | 91% | `all_jobs_list` route | `mdwiki` repo includes a global job list route. | Port the job list route back to `svg_translate_web`. | Merge directly |
| `profile.py` | 86% | Template usage | Minimal logic diffs. | Standardize profile view. | Standardize |

---

## Folder: shared

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `auth/mwoauth_handshake.py` | 94% | Logging verbosity | `mdwiki` repo has less logging. | Consolidate on the more verbose logging. | Merge directly |
| `decode_bytes.py` | 100% | None | Identical | None | Merge directly |

---

## Folder: su_services

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `jobs_files_service.py`| 97% | Path handling | Minor divergence in how `jobs_path` is accessed. | Standardize on the `settings.paths` object. | Merge directly |

---

## Folder: templates

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| `base.html` | 97% | Navbar title | Minor UI differences. | Move site title to config. | Refactor into shared base |
| `_navbar.html` | 79% | Menu items | Tool-specific links. | Pass navbar links as a list from the backend. | Refactor into shared component |
| `index.html` | 20% | Content | Main landing page is completely different. | Keep repository-specific. | Keep separate |

---

## Consolidation Opportunities

### Priority 1 (Immediate Merge Candidates)
*   `src/main_app/core/` (all files)
*   `src/main_app/db/services/utils/` (all files)
*   `src/main_app/db/models/jobs.py` and `settings.py`
*   `src/main_app/api_services/mwclient_page/`
*   `src/main_app/public/auth/` (OAuth logic)

### Priority 2 (Minor Refactoring Required)
*   `src/main_app/config/main_settings.py`: Extract WIKI_DOMAIN and Cookie Salt to environment variables.
*   `src/main_app/admin/sidebar.py`: Refactor to accept a list of tool-specific items.
*   `src/main_app/db/services/delete_service.py`: Standardize record deletion.

### Priority 3 (Shared Abstractions Recommended)
*   `src/main_app/jobs_workers/`: Both repos use the same `BaseJobWorker` pattern but implement different jobs. A shared base class package would be beneficial.

---

## Database Layer Analysis

*   **Models**: The core models (`JobRecord`, `SettingRecord`, `UsersRecord`, `UserTokenRecord`) are identical across both repositories. They use the same table names and column definitions.
*   **Services**: `jobs_service`, `settings_service`, and `users_service` are identical.
*   **ORM Patterns**: Both use SQLAlchemy 2.0 style mapping with `Mapped` and `mapped_column`.
*   **Query Logic**: Centralized in service files, using the same retry-on-disconnect and guard patterns.

**Opportunities**:
1.  **Shared Models Package**: Create a `mdwiki-db-models` package containing the core tables.
2.  **Common Service Layer**: Move the core services to the same package.
3.  **Standardize Migration**: Both use a similar `init_db` logic. This can be moved to a shared initialization utility.

---

## Synchronization Strategy

| Target Repository | Source Repository | Required Changes | Estimated Effort | Risk Level |
| ----------------- | ----------------- | ---------------- | ---------------- | ---------- |
| `svg_translate_web` | `mdwiki.org_scripts` | Port `import_page_from_wiki` to `query_api.py` | Low (1 hour) | Low |
| Both | Both | Move `core/` and `db/services/utils/` to a shared internal library | Medium (1 day) | Low |
| `svg_translate_web` | `mdwiki.org_scripts` | Port global job list route and template | Low (2 hours) | Low |
| Both | Both | Standardize `main_settings.py` env vars | Low (2 hours) | Medium |

---

## Final Recommendations

1.  **Shared Library**: Extract `api_services/mwclient_page`, `core/`, `db/services/utils/`, and `shared/auth` into a shared Python package (e.g., `mdwiki-common-web`).
2.  **Tool-Specific Logic**: Keep `jobs_workers/` and specialized model files (like `owid_charts.py`) repository-specific.
3.  **Estimated Maintenance Reduction**: **35-40%**.
4.  **Recommended Architecture**:
    ```
    mdwiki-common-web/
    ├── api/
    ├── core/
    ├── db/ (core models/services)
    └── auth/

    [Repo] svg_translate_web/
    ├── src/main_app/
    │   ├── jobs_workers/ (SVG/OWID specific)
    │   └── db/models/ (SVG/OWID specific)

    [Repo] mdwiki.org_scripts/
    ├── src/main_app/
    │   ├── jobs_workers/ (MDWiki specific)
    │   └── db/models/ (MDWiki specific)
    ```
5.  **Phased Migration Plan**:
    *   **Phase 1**: Align environment variable names and configuration defaults.
    *   **Phase 2**: Merge identical files and port minor missing features (like the job list).
    *   **Phase 3**: Extract shared logic into a common library.
    *   **Phase 4**: Update both repositories to depend on the common library.
