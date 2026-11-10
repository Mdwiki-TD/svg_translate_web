# api_services — MediaWiki API Integration

## Project Overview

MediaWiki API integration layer wrapping the `mwclient` library. Provides authenticated page operations, query helpers, and Wikimedia Commons utilities for the mdwiki.org toolset.

### Structure

```
api_services/
├── __init__.py         # Re-exports MwClientPage, get_user_site
├── mwclient_page/mwclient_wraper.py    # MwClientPage — page CRUD with rate-limit retry
├── pages_api.py        # High-level page operations
├── query_api.py        # Query API helpers (templates, redirects, search, links)
├── category.py         # Category member fetching
├── clients/
│   ├── __init__.py     # Re-exports
│   ├── wiki_client.py  # OAuth-authenticated mwclient.Site factory
│   └── commons_client.py # Wikimedia Commons session factory
└── utils/
    └── __init__.py     # Empty (placeholder)
```

## Key Components

### MwClientPage (`mwclient_page/mwclient_wraper.py`)

Wraps `mwclient.page.Page` with comprehensive error handling and rate-limit retry.

| Method                         | Description                                            |
| ------------------------------ | ------------------------------------------------------ |
| `load_page()`                  | Loads page from MediaWiki, handles `InvalidPageTitle`  |
| `check_exists()`               | Returns `True` if page exists                          |
| `is_redirect()`                | Checks if page is a redirect via `redirects_to()`      |
| `edit_page(text, summary)`     | Edits with rate-limit retry (3 attempts: 5s, 15s, 30s) |
| `move_page(new_title, reason)` | Moves/renames with rate-limit retry                    |

**Error handling**: Catches `ProtectedPageError`, `EditError`, `AssertUserFailedError`, `UserBlocked`, `APIError` (rate-limited).

### pages_api.py — High-Level Page Operations

| Function                                                   | Description               |
| ---------------------------------------------------------- | ------------------------- |
| `edit_page(site, title, text, summary)`                    | Edit a page               |
| `create_page(page_name, wikitext, site, summary)`          | Create a new page         |
| `move_page(site, title, new_title, ...)`                   | Move/rename a page        |
| `get_page_text(page_title, site)`                          | Get page wikitext         |
| `update_page_text(page_name, updated_text, site, summary)` | Update page content       |
| `import_page_from_wiki(site, title, family)`               | Import revision history   |
| `is_page_exists(page_title, site)`                         | Check page existence      |
| `is_redirect(page_title, site)`                            | Check if page is redirect |

All functions use `verify_required_fields()` for input validation.

### query_api.py — Query Helpers

| Function                                      | Description                                                    |
| --------------------------------------------- | -------------------------------------------------------------- |
| `get_template_pages(title, namespace, site)`  | Pages transcluding a template                                  |
| `is_pages_exists(titles, site)`               | Batch existence check (50 at a time)                           |
| `resolve_redirects(titles, site)`             | Batch redirect resolution                                      |
| `search_pages(query, site, namespace, limit)` | MediaWiki search API                                           |
| `get_double_redirects(site)`                  | Double redirect detection (returns resolved `from`→`to` pairs) |
| `get_page_links(title, site, namespace)`      | Wikilinks on a page                                            |

### category.py

`get_category_members( site: mwclient.Site, category_title: str, namespace: int = 0, )` — Paginated category member fetching using raw `requests`.

### clients/wiki_client.py

`get_user_site(user_dict)` → `mwclient.Site` — Creates an OAuth-authenticated mwclient connection. Decrypts stored tokens via Fernet.

## Testing

```bash
pytest tests/unit/api_services --cov=src/main_app/api_services
```

## Strengths

-   **Comprehensive rate-limit retry** with exponential backoff (5s → 15s → 30s)
-   **Specific exception handling** for MediaWiki error types
-   **Batch operations** for efficiency (50-page groups)
-   **Clean separation** between low-level (MwClientPage) and high-level (pages_api)
-   **Proper field validation** before API calls

## Weaknesses

-   **Broken function** — `get_template_pages_newapi()` calls `api = None; api.NewApi()`
-   **Inconsistent HTTP clients** — `category.py` uses raw `requests` while others use `mwclient`
-   **Empty `utils/` package** — dead code
-   **No response caching** — repeated queries for the same data
-   **`get_page_text` returns empty string** on error — callers can't distinguish empty page from error
-   **No retry logic** for non-rate-limit API errors

## Critical Issues

> **Warning**: `get_template_pages_newapi()` will crash with `AttributeError`.

```python
# query_api.py lines 28-29
api = None  # get_api()
results = api.NewApi().post_continue(...)  # AttributeError!
```

## Areas That Need Attention

-   [x] Remove `get_template_pages_newapi()`
-   [ ] Remove empty `utils/` package
-   [ ] Add caching for repeated queries
-   [ ] Make `get_page_text` raise on error instead of returning empty string
-   [ ] Unify HTTP client usage (mwclient everywhere)

## Improvement Plan

### Quick Wins

1. Remove or fix `get_template_pages_newapi()`
2. Remove empty `utils/__init__.py`

### Medium-Term

1. Add response caching with TTL
2. Add retry logic for transient API errors
3. Standardize error return patterns

### Long-Term

1. Add async support for batch operations
2. Add rate-limit tracking across requests

## Comprehensive Review

| Metric                   | Score               |
| ------------------------ | ------------------- |
| **Overall Rating**       | **6.5/10**          |
| **Production Readiness** | Moderate            |
| **Error Handling**       | Good (MwClientPage) |
| **API Coverage**         | Comprehensive       |
| **Maintainability**      | 6/10                |
