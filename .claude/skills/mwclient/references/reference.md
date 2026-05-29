---
name: mwclient-api-reference
description: Complete API reference for the mwclient library — all classes, methods, parameters, and return types.
applies_to:
    - "Site"
    - "Page"
    - "Image"
    - "Category"
    - "mwclient"
---

# mwclient API Reference

Full method signatures and parameter documentation for mwclient 0.11.0.

## Table of Contents

1. [Site](#site)
2. [Page](#page)
3. [Image](#image)
4. [Category](#category)
5. [Listing Classes](#listing-classes)
6. [Exceptions](#exceptions)

---

## Site

**Module**: `mwclient.client` · **Import**: `mwclient.Site`

### Constructor

```python
Site(
    host: str,                                    # Required. Hostname only, no scheme/path
    path: str = '/w/',                            # Script path, must end with /
    ext: str = '.php',                            # File extension
    scheme: str = 'https',                        # URI scheme
    pool: requests.Session = None,                # Reuse existing session
    retry_timeout: int = 30,                      # Seconds per retry level
    max_retries: int = 25,                        # Max retry attempts
    wait_callback: Callable = lambda *x: None,    # Called before each retry sleep
    clients_useragent: str = None,                # Prepend to default user-agent
    max_lag: int = 3,                             # MediaWiki maxlag parameter
    compress: bool = True,                        # Request gzip responses
    force_login: bool = True,                     # Require auth for writes
    do_init: bool = True,                         # Auto-call site_init()
    httpauth: tuple | AuthBase = None,            # HTTP Basic or custom auth
    connection_options: dict = None,               # Passed to requests.Session
    consumer_token: str = None,                   # OAuth 1 consumer token
    consumer_secret: str = None,                  # OAuth 1 consumer secret
    access_token: str = None,                     # OAuth 1 access token
    access_secret: str = None,                    # OAuth 1 access secret
    client_certificate: str | tuple = None,       # SSL client cert path or (cert, key)
    custom_headers: dict = None,                  # Extra HTTP headers
)
```

### Attributes

| Attribute         | Type        | Description                                         |
| ----------------- | ----------- | --------------------------------------------------- |
| `site.pages`      | `PageList`  | Pages in namespace 0. Supports `['Title']` indexing |
| `site.categories` | `PageList`  | Categories (namespace 14)                           |
| `site.images`     | `PageList`  | Files (namespace 6)                                 |
| `site.logged_in`  | `bool`      | Whether currently authenticated                     |
| `site.blocked`    | `bool`      | Whether current user is blocked                     |
| `site.hasmsg`     | `bool`      | Whether user has unread messages                    |
| `site.rights`     | `list[str]` | Current user's rights                               |
| `site.groups`     | `list[str]` | Current user's groups                               |
| `site.username`   | `str`       | Current username                                    |
| `site.email`      | `str`       | Current user's email                                |
| `site.lang`       | `str`       | Wiki language code                                  |
| `site.mw_version` | `tuple`     | MediaWiki version                                   |
| `site.api_limit`  | `int`       | Max items per API request (500)                     |
| `site.chunk_size` | `int`       | Upload chunk size (1 MiB)                           |

### Authentication

```python
site.login(username=None, password=None, cookies=None, domain=None)
```

Bot password login. Handles MW 1.27+ token flow. Retries on throttling. Calls `site_init()` on success.

```python
site.clientlogin(cookies=None, **kwargs)
```

MW 1.27+ clientlogin flow. Pass `username=` and `password=`. Returns `True` on success, raises `LoginError` on failure, returns dict for multi-step flows (`UI`/`REDIRECT`).

```python
site.get_token(type: str, force=False, title=None) -> str
```

Get a token (`'csrf'`, `'login'`, `'email'`). Cached in `site.tokens`; cleared on `site_init()`.

### API Methods

```python
site.get(action, **kwargs) -> dict
```

Shorthand for `api(action, 'GET', ...)`. For idempotent reads.

```python
site.post(action, **kwargs) -> dict
```

Shorthand for `api(action, 'POST', ...)`. For writes.

```python
site.api(action, http_method='POST', **kwargs) -> dict
```

Primary interface. Auto-injects `continue=''` and `userinfo` on queries. Retry loop via `Sleeper`.

```python
site.raw_api(action, http_method='POST', retry_on_error=True, *args, **kwargs) -> dict
```

Low-level. Adds `format=json`, calls `raw_call`, parses JSON. Raises `APIDisabledError` if API disabled.

```python
site.raw_call(script, data, files=None, retry_on_error=True, http_method='POST') -> str
```

Lowest HTTP layer. Handles 5xx/429/DB-lag/ConnectionError/Timeout with retry.

### Site-Level Listing Methods

All return lazy `List` or `GeneratorList` iterators. Common params: `max_items`, `api_chunk_size`, `generator`.

```python
site.allpages(start=None, prefix=None, namespace=None, redirects='all', end=None,
              filterredir=None, filterlanglinks=None, minsize=None, maxsize=None,
              prtype=None, prlevel=None, dir='ascending', protection=None,
              max_items=None, api_chunk_size=None, generator=True)
```

```python
site.allimages(start=None, prefix=None, minsize=None, maxsize=None, dir='ascending',
               sha1=None, sha1base36=None, mime=None, max_items=None, api_chunk_size=None)
```

```python
site.alllinks(start=None, prefix=None, unique=False, prop='title', namespace=None,
              max_items=None, api_chunk_size=None)
```

```python
site.allcategories(start=None, prefix=None, dir='ascending', min=None, max=None,
                   max_items=None, api_chunk_size=None)
```

```python
site.allusers(start=None, prefix=None, group=None, prop=None, rights=None,
              witheditsonly=False, activeusers=False, max_items=None, api_chunk_size=None)
```

```python
site.recentchanges(start=None, end=None, dir='older', namespace=None,
                   prop='title|timestamp|ids', show=None, type=None,
                   toponly=None, max_items=None, api_chunk_size=None)
```

```python
site.logevents(type=None, start=None, end=None, dir='older', user=None, title=None,
               action=None, prop='type|user|timestamp|details', max_items=None,
               api_chunk_size=None)
```

```python
site.blocks(start=None, end=None, users=None, ip=None, props=None,
            max_items=None, api_chunk_size=None)
```

```python
site.deletedrevisions(start=None, end=None, dir='older', namespace=None, user=None,
                      fromuser=None, prop=None, max_items=None, api_chunk_size=None)
```

```python
site.exturlusage(query=None, prop='url|title', protocol=None, namespace=None,
                 max_items=None, api_chunk_size=None)
```

```python
site.usercontributions(user, start=None, end=None, dir='older', namespace=None,
                       prop='title|timestamp|comment|size', show=None, topOnly=None,
                       max_items=None, api_chunk_size=None)
```

```python
site.random(namespace=None, redirect='all', max_items=None, api_chunk_size=None)
```

```python
site.search(search, namespace=None, what=None, redirects=False,
            max_items=None, api_chunk_size=None)
```

```python
site.users(users, prop='blockinfo|groups|editcount|registration|rights')
```

```python
site.revisions(revids) -> list[dict]
```

Not a generator. Returns a plain list of revision dicts.

```python
site.watchlist(allrev=False, start=None, end=None, namespace=None, owner=None,
               token=None, max_items=None, api_chunk_size=None)
```

### Utility Methods

```python
site.expandtemplates(text, title=None, generatexml=False) -> str | tuple
```

```python
site.parse(text, title=None, ...) -> dict
```

```python
site.patrol(rcid=None, revid=None) -> dict
```

```python
site.email(user, subject, text, ccme=False) -> dict
```

```python
site.ask(query, title=None) -> GeneratorList
```

Semantic MediaWiki ask query. Returns generator of result dicts.

### Upload

```python
site.upload(
    file: str | BinaryIO = None,    # File path or file object
    filename: str = None,           # Target filename on wiki
    description: str = '',          # File description page text
    comment: str = None,            # Upload log comment
    ignore: bool = False,           # Ignore FileExists warning
    url: str = None,                # URL for server-side fetch
    filekey: str = None,            # Stash filekey for two-phase upload
    stash: bool = False,            # Stash without publishing
    asynchronous: bool = False,     # Background finalization
) -> dict
```

Exactly one of `file`, `url`, or `filekey` must be provided. Files larger than `chunk_size` (1 MiB) are automatically chunked.

---

## Page

**Module**: `mwclient.page` · **Obtained via**: `site.pages['Title']` or `site.pages.get('Title')`

### Constructor

```python
Page(site: Site, name: int | str | Page, info: dict = None, extra_properties: dict = None)
```

-   `name` can be a title string, page ID (int), or another Page object
-   If `info` is None, fetches `prop=info&inprop=protection` from API
-   Pages from listings/generators have `info` pre-fetched (no extra API call)

### Attributes

| Attribute               | Type   | Description                         |
| ----------------------- | ------ | ----------------------------------- |
| `page.name`             | `str`  | Full page title (e.g. `"Talk:Foo"`) |
| `page.page_title`       | `str`  | Title without namespace prefix      |
| `page.base_title`       | `str`  | Title without subpage suffix        |
| `page.base_name`        | `str`  | `base_title` without namespace      |
| `page.namespace`        | `int`  | Namespace number                    |
| `page.exists`           | `bool` | Whether page exists                 |
| `page.pageid`           | `int`  | Page ID (0 if not exists)           |
| `page.revision`         | `dict` | Current revision info               |
| `page.length`           | `int`  | Page size in bytes                  |
| `page.touched`          | `str`  | Last touched timestamp              |
| `page.protection`       | `list` | Protection settings                 |
| `page.redirect`         | `bool` | Whether page is a redirect          |
| `page.contentmodel`     | `str`  | Content model (e.g. `"wikitext"`)   |
| `page.pagelanguage`     | `str`  | Page language code                  |
| `page.restrictiontypes` | `list` | Available restriction types         |

### Reading

```python
page.text(section=None, expandtemplates=False, cache=True, slot='main') -> str
```

Returns wikitext. Returns `''` for non-existent pages. `section` can be int or string. `cache=False` forces fresh API call. Results cached in `page._textcache`.

### Writing

```python
page.edit(text, summary='', minor=False, bot=True, section=None, **kwargs)
page.save(text, summary='', minor=False, bot=True, section=None, **kwargs)  # alias
```

Full page replace. Checks `force_login`, `blocked`, `can('edit')`. Handles edit conflicts via `basetimestamp`/`starttimestamp`. On `badtoken`, auto-refreshes token and retries once.

```python
page.append(text, summary='', minor=False, bot=True, section=None, **kwargs)
```

Appends text (uses `appendtext` parameter).

```python
page.prepend(text, summary='', minor=False, bot=True, section=None, **kwargs)
```

Prepends text (uses `prependtext` parameter).

```python
page.touch()
```

Null edit. Updates parser cache without changing content.

### Page Management

```python
page.move(new_title, reason='', move_talk=True, no_redirect=False,
          move_subpages=False, ignore_warnings=False)
```

Checks `can('move')`. Raises `InsufficientPermission` on failure.

```python
page.delete(reason='', watch=False, unwatch=False, oldimage=None)
```

Checks `can('delete')`. Sets `page.exists = False` on success.

```python
page.purge()
```

Invalidates parser cache (`action=purge`).

### Permissions

```python
page.can(action: str) -> bool
```

Checks if current user has the required protection level. `action` is `'edit'`, `'move'`, `'delete'`, etc. Maps `'sysop'` to `'editprotected'`.

### Redirects

```python
page.redirects_to() -> Page | None
page.resolve_redirect() -> Page
```

`resolve_redirect()` follows the chain and returns self if not a redirect.

### Page Property Iterators

All return lazy iterators. Common params: `max_items`, `api_chunk_size`, `generator`.

```python
page.backlinks(namespace=None, filterredir=None, redirect=None, generator=True,
               max_items=None, api_chunk_size=None)
```

```python
page.categories(generator=True, show=None)
```

```python
page.embeddedin(namespace=None, filterredir=None, generator=True,
                max_items=None, api_chunk_size=None)
```

```python
page.extlinks()
```

```python
page.images(generator=True)
```

```python
page.iwlinks()
```

```python
page.langlinks()
```

```python
page.links(namespace=None, generator=True, redirects=None)
```

```python
page.templates(namespace=None, generator=True)
```

### Revisions

```python
page.revisions(startid=None, endid=None, start=None, end=None, dir='older',
               user=None, excludeuser=None, prop='ids|timestamp|size|user|comment',
               expandtemplates=False, section=None, diffto=None, slots=None,
               uselang=None, max_items=None, api_chunk_size=None)
```

Returns `RevisionsIterator`. Fetches revision history with content.

---

## Image

**Module**: `mwclient.image` · **Extends**: `Page` · **Obtained via**: `site.images['File:Name.jpg']`

### Attributes

| Attribute               | Type   | Description                                           |
| ----------------------- | ------ | ----------------------------------------------------- |
| `image.imageinfo`       | `dict` | First item of imageinfo (url, size, sha1, mime, etc.) |
| `image.imagerepository` | `str`  | `'local'`, `'shared'`, or `''`                        |

### Methods

```python
image.imagehistory() -> PageProperty
```

Returns iterator of past file revision dicts.

```python
image.imageusage(namespace=None, filterredir=None, redirect=None,
                 max_items=None, api_chunk_size=None, generator=True)
```

Pages that use this file.

```python
image.duplicatefiles(max_items=None, api_chunk_size=None)
```

Byte-identical files.

```python
image.download(destination=None) -> bytes | None
```

If `destination` (a file handle) is given, streams in 1024-byte chunks. Otherwise loads entire file into memory. For large files, prefer streaming.

---

## Category

**Module**: `mwclient.listing` · **Extends**: `Page`, `GeneratorList` · **Obtained via**: `site.categories['Name']`

When iterated directly (`for member in cat`), yields category members as `Page`/`Image`/`Category` objects.

### Methods

```python
cat.members(prop='ids|title', namespace=None, sort='sortkey', dir='asc',
            start=None, end=None, generator=True) -> List | GeneratorList
```

Returns iterable of category members. `generator=True` yields page objects; `generator=False` yields dicts.

---

## Listing Classes

**Module**: `mwclient.listing`

### List

Base lazy iterator. Fetches data in chunks from the MediaWiki API, following continuation tokens automatically.

```python
List(site, list_name, prefix, limit=None, return_values=None,
     max_items=None, api_chunk_size=None, **kwargs)
```

-   `max_items`: Cap total items yielded
-   `api_chunk_size`: Items per API call (defaults to `min(max_items, site.api_limit)`)
-   `return_values`: What to yield — `None` (full dict), `'title'` (string), `('title', 'ns')` (tuple)
-   `limit`: Deprecated. Use `api_chunk_size` + `max_items`

### GeneratorList

Extends `List`. Yields `Page`, `Image`, or `Category` objects based on namespace. Namespace 6 → `Image`, 14 → `Category`, else → `Page`.

### PageList

```python
PageList(site, prefix=None, start=None, namespace=0, redirects='all', end=None)
```

Used for `site.pages`, `site.categories`, `site.images`. Supports `__getitem__` for direct access: `site.pages['Title']`.

### PageProperty / PagePropertyGenerator

Used for page-level properties (revisions, links, categories, etc.). Sets `titles=page.name`.

### RevisionsIterator

Specialized `PageProperty` for revision queries. Handles `rvstartid`/`rvstart` conflicts.

### NestedList

For API responses with a nested key (e.g., `checkuserlog` → `entries`).

---

## Exceptions

**Module**: `mwclient.errors` · **Import**: `mwclient.APIError`, etc.

All inherit from `MwClientError` (which inherits from `RuntimeError`).

| Exception                 | Attributes               | Raised When                                                        |
| ------------------------- | ------------------------ | ------------------------------------------------------------------ |
| `MwClientError`           | —                        | Base class for all mwclient errors                                 |
| `MediaWikiVersionError`   | —                        | Unsupported MW version                                             |
| `APIDisabledError`        | —                        | API returns non-JSON (API disabled)                                |
| `MaximumRetriesExceeded`  | —                        | All retry attempts exhausted                                       |
| `APIError`                | `code`, `info`, `kwargs` | API returns an error response                                      |
| `InsufficientPermission`  | —                        | User lacks required right                                          |
| `UserBlocked`             | —                        | Current user is blocked (extends `InsufficientPermission`)         |
| `EditError`               | —                        | Edit failed (conflict, etc.)                                       |
| `ProtectedPageError`      | —                        | Page is protected (extends `EditError` + `InsufficientPermission`) |
| `FileExists`              | `file_name`              | Upload target already exists, `ignore=False`                       |
| `LoginError`              | `site`, `code`, `info`   | Login failed                                                       |
| `OAuthAuthorizationError` | —                        | OAuth credentials invalid (extends `LoginError`)                   |
| `AssertUserFailedError`   | —                        | Not logged in, `force_login=True`                                  |
| `EmailError`              | —                        | Email sending failed                                               |
| `NoSpecifiedEmail`        | —                        | Target user has no email (extends `EmailError`)                    |
| `InvalidResponse`         | `response_text`          | Non-JSON response from API                                         |
| `InvalidPageTitle`        | —                        | Invalid page title provided                                        |
