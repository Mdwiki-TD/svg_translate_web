---
name: mwclient-error-handling
description: Handling errors, exceptions, retries, and edge cases in mwclient — APIError, ProtectedPageError, edit conflicts, retry logic, blocked users, and graceful degradation.
applies_to:
    - "error"
    - "exception"
    - "retry"
    - "APIError"
    - "ProtectedPageError"
    - "EditError"
    - "LoginError"
    - "MaximumRetriesExceeded"
    - "blocked"
    - "conflict"
---

# Error Handling

## When to use this file

When the user needs to catch errors, handle retries, deal with protected pages, manage edit conflicts, or build robust error handling around mwclient operations.

## Mental model

mwclient has two retry layers (transport and application) and a structured exception hierarchy. Transport-level issues (5xx, timeouts, DB lag) are retried automatically. Application-level errors (API errors, permission issues) raise specific exceptions. The `Sleeper` class handles linear backoff across both layers.

## Quick reference

| Situation         | Exception                   | Action                           |
| ----------------- | --------------------------- | -------------------------------- |
| Not logged in     | `AssertUserFailedError`     | Call `site.login()`              |
| User blocked      | `UserBlocked`               | Check `site.blocked`             |
| Page protected    | `ProtectedPageError`        | Check `page.can('edit')`         |
| Edit conflict     | `EditError`                 | Re-read `page.text()` and retry  |
| File exists       | `FileExists`                | Use `ignore=True`                |
| Login failed      | `LoginError`                | Check credentials                |
| API error         | `APIError`                  | Check `e.code`, `e.info`         |
| Retries exhausted | `MaximumRetriesExceeded`    | Increase `max_retries` or handle |
| Bad token         | `APIError(code='badtoken')` | Force token refresh              |

## Exception hierarchy

```
MwClientError (RuntimeError)
  +-- MediaWikiVersionError
  +-- APIDisabledError
  +-- MaximumRetriesExceeded
  +-- APIError                    (.code, .info, .kwargs)
  +-- InsufficientPermission
  |     +-- UserBlocked
  +-- EditError
  |     +-- ProtectedPageError    (also InsufficientPermission)
  |     +-- FileExists            (.file_name)
  +-- LoginError                  (.site, .code, .info)
  |     +-- OAuthAuthorizationError
  +-- AssertUserFailedError
  +-- EmailError
  |     +-- NoSpecifiedEmail
  +-- InvalidResponse             (.response_text)
  +-- InvalidPageTitle
```

## Catching errors

### Edit errors

```python
from mwclient import errors

try:
    page.save('New content', summary='Editing')
except errors.ProtectedPageError:
    print(f"Page {page.name} is protected")
except errors.EditError as e:
    print(f"Edit failed: {e}")
except errors.APIError as e:
    print(f"API error: {e.code} — {e.info}")
```

### Login errors

```python
try:
    site.login('Bot', 'wrong_password')
except errors.LoginError as e:
    print(f"Login failed: {e.code} — {e.info}")
except errors.OAuthAuthorizationError:
    print("OAuth credentials are invalid")
```

### Upload errors

```python
try:
    with open('image.jpg', 'rb') as f:
        site.upload(f, 'Image.jpg', description='Photo')
except errors.FileExists:
    print("File already exists")
except errors.InsufficientPermission:
    print("No upload permission")
```

### Catch-all for mwclient errors

```python
try:
    page.save('content', summary='edit')
except errors.MwClientError as e:
    print(f"mwclient error: {type(e).__name__}: {e}")
```

## Edit conflict handling

Edit conflicts happen when someone edits a page between your `text()` and `save()` calls:

```python
page = site.pages['Some Page']
old_text = page.text()  # Sets basetimestamp for conflict detection

new_text = old_text.replace('old value', 'new value')
try:
    page.save(new_text, summary='Updating value')
except errors.EditError:
    # Conflict — re-read and retry
    page = site.pages[page.name]  # Fresh page object
    old_text = page.text()
    new_text = old_text.replace('old value', 'new value')
    page.save(new_text, summary='Updating value (retry after conflict)')
```

## Bad token recovery

The library handles `badtoken` automatically during edits — it force-refreshes the CSRF token and retries once. For other operations:

```python
try:
    site.post('someaction', token=site.get_token('csrf'), ...)
except errors.APIError as e:
    if e.code == 'badtoken':
        site.get_token('csrf', force=True)
        site.post('someaction', token=site.get_token('csrf'), ...)
    else:
        raise
```

## Blocked user handling

```python
site = mwclient.Site('en.wikipedia.org')
site.login('MyBot', 'password')

if site.blocked:
    print(f"Bot is blocked — cannot edit")
    # site.blocked contains block info or True
else:
    page = site.pages['Some Page']
    page.save('content', summary='edit')
```

## Retry mechanism

### How retries work

Two independent retry layers:

1. **Transport** (`raw_call`): Retries on HTTP 5xx, 429, DB lag headers, `ConnectionError`, `Timeout`
2. **Application** (`api` + `handle_api_result`): Retries on `DBConnectionError`, `DBQueryError`, OAuth nonce reuse

Both use linear backoff: `sleep = retry_timeout * (retries - 1)`.

| Retry # | Default sleep (seconds)         |
| ------- | ------------------------------- |
| 1       | 0                               |
| 2       | 30                              |
| 3       | 60                              |
| ...     | ...                             |
| 25      | 720                             |
| 26      | raises `MaximumRetriesExceeded` |

### Customize retry behavior

```python
site = mwclient.Site(
    'en.wikipedia.org',
    max_retries=10,         # Default 25
    retry_timeout=15,       # Default 30 seconds per level
)
```

### Retry callback for logging

```python
def log_retries(sleeper, retries, args):
    print(f"Retry {retries}/{sleeper.max_retries} — sleeping {sleeper.retry_timeout * retries}s")

site = mwclient.Site('en.wikipedia.org', wait_callback=log_retries)
```

The callback is called before each sleep. Raise an exception inside it to cancel retries.

### Handle MaximumRetriesExceeded

```python
try:
    page.save('content', summary='edit')
except errors.MaximumRetriesExceeded:
    print("Server too busy — try again later")
```

## Permission checks

### Pre-flight permission check

```python
page = site.pages['Protected Page']
if not page.can('edit'):
    print(f"Cannot edit — protection level too high")
    print(f"Page protection: {page.protection}")
else:
    page.save('content', summary='edit')
```

### Check site-level permissions

```python
if 'upload' in site.rights:
    print("Can upload files")
if 'delete' in site.rights:
    print("Can delete pages")
```

## Graceful degradation patterns

### Skip inaccessible pages

```python
for page in site.allpages(prefix='Protected/', max_items=100):
    try:
        text = page.text()
        # Process text
    except errors.InsufficientPermission:
        print(f"Skipping {page.name} — no read permission")
        continue
```

### Retry on transient failures

```python
import time

for attempt in range(3):
    try:
        page.save('content', summary='edit')
        break
    except errors.APIError as e:
        if e.code in ('ratelimited', 'actionthrottledtext'):
            time.sleep(30)
            continue
        raise
```

### Handle missing pages gracefully

```python
page = site.pages['Maybe Exists']
text = page.text()  # Returns '' for non-existent pages, no exception
if page.exists:
    process(text)
else:
    print(f"Page does not exist — creating")
    page.save('Initial content', summary='Creating page')
```

## Edge cases and gotchas

-   **`ProtectedPageError` has dual inheritance**: It extends both `EditError` and `InsufficientPermission`. Catch it with either parent, but `except InsufficientPermission` won't catch other `EditError` subtypes.
-   **`FileExists` is a client-side check**: mwclient raises it when `ignore=False` and the file exists. MediaWiki itself returns a warning, not an error.
-   **DB errors are retried silently**: `DBConnectionError` and `DBQueryError` don't surface to your code unless retries are exhausted.
-   **OAuth nonce reuse**: Retried automatically (Phabricator T106066). No action needed.
-   **`force_login=True` (default)**: Raises `AssertUserFailedError` before the edit API call even happens. Set `force_login=False` for anonymous edits.
-   **`MaximumRetriesExceeded` wraps the original exception**: The original cause (5xx, timeout, etc.) is in the exception's `__cause__`.

## See also

-   [01-connection-auth.md](01-connection-auth.md) — Login error handling
-   [02-page-operations.md](02-page-operations.md) — Edit conflict detection
-   [04-file-operations.md](04-file-operations.md) — Upload error handling
-   [../references/reference.md](../references/reference.md) — Full exception hierarchy with attributes
