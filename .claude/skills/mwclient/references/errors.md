# Error Handling

## Overview

This reference covers exception handling in mwclient. All mwclient-specific exceptions inherit from `MwClientError`, which extends Python's built-in `RuntimeError`. This allows catching all library errors with a single `except MwClientError` clause.

**Key Files:**

-   `mwclient/errors.py` - Exception class definitions

## Exception Hierarchy

```
RuntimeError
└── MwClientError (base for all mwclient errors)
    ├── MediaWikiVersionError
    ├── APIDisabledError
    ├── MaximumRetriesExceeded
    ├── APIError
    ├── InsufficientPermission
    │   └── UserBlocked
    ├── EditError
    │   ├── ProtectedPageError (also inherits from InsufficientPermission)
    │   └── FileExists
    ├── LoginError
    │   └── OAuthAuthorizationError
    ├── AssertUserFailedError
    ├── EmailError
    │   └── NoSpecifiedEmail
    ├── InvalidResponse
    └── InvalidPageTitle
```

## Exception Groups

| Group                    | Base Class               | Covers                                         |
| ------------------------ | ------------------------ | ---------------------------------------------- |
| Connection/compatibility | `MwClientError`          | Version errors, API disabled, invalid response |
| API-level errors         | `APIError`               | Any error object in API JSON response          |
| Permission errors        | `InsufficientPermission` | Blocked users, protected pages, missing rights |
| Edit errors              | `EditError`              | Failed edits, captcha, file conflicts          |
| Authentication errors    | `LoginError`             | Login failure, OAuth rejection                 |

## Exception Reference

### MwClientError

Base class for the entire hierarchy. Catching `MwClientError` catches all library-specific errors.

```python
try:
    # mwclient operation
    pass
except mwclient.errors.MwClientError as e:
    print(f"Mwclient error: {e}")
```

### APIError

Raised when the MediaWiki API response contains a top-level `"error"` key.

**Attributes:**

| Attribute | Type            | Description                                     |
| --------- | --------------- | ----------------------------------------------- |
| `code`    | `Optional[str]` | The `error.code` field from API response        |
| `info`    | `str`           | The `error.info` field (human-readable message) |
| `kwargs`  | `Optional[Any]` | Full raw error dict from response               |

```python
try:
    site.post('edit', title='Page', text='Content')
except mwclient.errors.APIError as e:
    print(f"API error {e.code}: {e.info}")
```

### MediaWikiVersionError

Raised during site initialization when the MediaWiki version string cannot be parsed or is below the minimum supported (1.16).

### APIDisabledError

Raised by `site_init()` when the API response is plain text like `"MediaWiki API is not enabled for this site."` instead of valid JSON.

### MaximumRetriesExceeded

Raised when the retry count exceeds `max_retries`. This can occur at:

-   **Transport level** - 5xx errors or database lag retries exhausted
-   **Application level** - `DBConnectionError` retries exhausted

### InsufficientPermission

Raised when the current user lacks a required permission.

```python
try:
    site.upload(file=f, filename='test.jpg')
except mwclient.errors.InsufficientPermission:
    print("User cannot upload files")
```

### UserBlocked

Subclass of `InsufficientPermission`. Raised when an action is attempted while the user account is blocked.

```python
try:
    page.edit('New content')
except mwclient.errors.UserBlocked as e:
    print("User is blocked")
```

### EditError

Base class for errors during page editing. Catching `EditError` also catches `ProtectedPageError` and `FileExists`.

### ProtectedPageError

Raised when an edit attempt returns protection-related error codes like `protectedpage`, `protectednamespace`, etc.

**Multiple inheritance:** `ProtectedPageError` inherits from _both_ `EditError` and `InsufficientPermission`.

**Attributes:**

| Attribute | Type            | Description                                 |
| --------- | --------------- | ------------------------------------------- |
| `page`    | `Page`          | The page object on which edit was attempted |
| `code`    | `Optional[str]` | API error code (e.g., `'protectedpage'`)    |
| `info`    | `Optional[str]` | API error info string                       |

```python
try:
    page.edit('Content')
except mwclient.errors.ProtectedPageError as e:
    print(f"Cannot edit {e.page.name}: {e.info}")
```

### FileExists

Subclass of `EditError`. Raised by `site.upload()` when a file already exists and `ignore=False`.

**Attribute:** `file_name` - the name of the conflicting file.

```python
try:
    site.upload(file=f, filename='existing.jpg')
except mwclient.errors.FileExists as e:
    print(f"File {e.file_name} exists")
    # Retry with ignore=True to overwrite
    site.upload(file=f, filename='existing.jpg', ignore=True)
```

### LoginError

Raised by `site.login()` and `site.clientlogin()` when login fails (status `FAIL`).

**Attributes:**

| Attribute | Type            | Description                               |
| --------- | --------------- | ----------------------------------------- |
| `site`    | `Site`          | The Site object where login was attempted |
| `code`    | `Optional[str]` | Result/error code from response           |
| `info`    | `str`           | Human-readable failure reason             |

```python
try:
    site.login('user', 'pass')
except mwclient.errors.LoginError as e:
    print(f"Login failed: {e.info}")
```

### OAuthAuthorizationError

Subclass of `LoginError`. Raised when OAuth-authenticated request receives an authorization error.

### AssertUserFailedError

Raised when the API returns `assertuserfailed`. This means an edit was attempted without being logged in while `force_login=True` (the default).

```python
try:
    page.edit('Content')
except mwclient.errors.AssertUserFailedError:
    print("Must be logged in to edit")
```

### EmailError / NoSpecifiedEmail

`EmailError` is the base class for email failures. `NoSpecifiedEmail` is raised when attempting to email a user who hasn't set up an email address.

### InvalidResponse

Raised when the server returns a response that cannot be decoded as JSON. The raw text is stored in `response_text`.

**Common cause:** Wrong hostname or path, or server redirecting to login page.

```python
try:
    site = mwclient.Site('invalid.host.example')
except mwclient.errors.InvalidResponse as e:
    print(f"Invalid response: {e.response_text[:100]}")
```

### InvalidPageTitle

Raised by `Page.__init__()` when the API returns an `"invalid"` key, indicating the title contains illegal characters.

## Catching Patterns

### Catch all mwclient errors

```python
import mwclient.errors as errors

try:
    # Any mwclient operation
    page = site.pages['Page']
    page.edit('Content')
except errors.MwClientError as e:
    print(f"Mwclient error: {e}")
```

### Specific error handling

```python
try:
    page.edit('New content', summary='Edit')
except errors.ProtectedPageError:
    print("Page is protected")
except errors.AssertUserFailedError:
    print("Not logged in")
except errors.UserBlocked:
    print("User is blocked")
except errors.EditError as e:
    print(f"Other edit error: {e}")
```

### Permission-based handling

```python
try:
    page.delete()
except errors.InsufficientPermission:
    print("Cannot delete page - insufficient rights")
```

### Upload error handling

```python
try:
    result = site.upload(file=f, filename='test.jpg')
except errors.InsufficientPermission:
    print("No upload permission")
except errors.FileExists as e:
    print(f"File {e.file_name} already exists")
    # Option to overwrite
    site.upload(file=f, filename='test.jpg', ignore=True)
except errors.APIError as e:
    print(f"API error: {e.code} - {e.info}")
```

### Login error handling

```python
try:
    site.login('username', 'password')
except errors.LoginError as e:
    print(f"Login failed: {e.info}")
    # Check specific error codes
    if e.code == 'Failed':
        print("Invalid credentials")
    elif e.code == 'Throttled':
        print("Too many attempts - wait before retrying")
```

### Connection error handling

```python
try:
    site = mwclient.Site('example.org')
except errors.APIDisabledError:
    print("API is disabled on this wiki")
except errors.MediaWikiVersionError:
    print("MediaWiki version too old")
except errors.InvalidResponse as e:
    print(f"Unexpected response: {e.response_text[:200]}")
except errors.MaximumRetriesExceeded:
    print("Connection failed after maximum retries")
```

## Error Summary Table

| Scenario               | Exception to Catch       | Key Attributes                                 |
| ---------------------- | ------------------------ | ---------------------------------------------- |
| Edit on protected page | `ProtectedPageError`     | `.page`, `.code`, `.info`                      |
| Not logged in          | `AssertUserFailedError`  | message in `.args[0]`                          |
| Any edit failure       | `EditError`              | catches `ProtectedPageError` and `FileExists`  |
| Any permission failure | `InsufficientPermission` | catches `UserBlocked` and `ProtectedPageError` |
| Upload duplicate       | `FileExists`             | `.file_name`                                   |
| Wrong credentials      | `LoginError`             | `.code`, `.info`                               |
| API returns error      | `APIError`               | `.code`, `.info`                               |
| Non-JSON response      | `InvalidResponse`        | `.response_text`                               |
| Retries exhausted      | `MaximumRetriesExceeded` | —                                              |
| API disabled           | `APIDisabledError`       | —                                              |
| MW too old             | `MediaWikiVersionError`  | —                                              |
| Invalid title          | `InvalidPageTitle`       | —                                              |

## TYPE_CHECKING Pattern

The errors module uses `TYPE_CHECKING` to avoid circular imports:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import mwclient.page
    import mwclient.client
```

Type annotations use string literals (forward references):

-   `ProtectedPageError.__init__(self, page: 'mwclient.page.Page', ...)`
-   `LoginError.__init__(self, site: 'mwclient.client.Site', ...)`

This allows the module to be imported anywhere while still providing type information to static checkers.
