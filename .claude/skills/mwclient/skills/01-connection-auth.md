---
name: mwclient-connection-auth
description: Connecting to MediaWiki sites and authenticating with mwclient — OAuth, bot passwords, clientlogin, HTTP auth, SSL certs, and session management.
applies_to:
    - "Site"
    - "login"
    - "clientlogin"
    - "OAuth"
    - "authenticate"
    - "connect"
    - "session"
---

# Connection and Authentication

## When to use this file

When the user needs to connect to a MediaWiki site, authenticate, configure session options, or handle private wikis.

## Mental model

`mwclient.Site` is the single entry point. It wraps a `requests.Session` and manages the full lifecycle: URL construction, authentication, token caching, and retry logic. Authentication happens either through constructor parameters (OAuth, HTTP auth) or method calls (`login()`, `clientlogin()`). The `site_init()` call (automatic by default) queries the API for user info, rights, and wiki metadata.

## Quick reference

| Task              | Code                                                              |
| ----------------- | ----------------------------------------------------------------- |
| Public wiki       | `site = mwclient.Site('en.wikipedia.org')`                        |
| Bot password      | `site = mwclient.Site('wiki.org'); site.login('Bot', 'pass')`     |
| OAuth 1           | `mwclient.Site('wiki.org', consumer_token=..., access_token=...)` |
| Client login      | `site.clientlogin(username='u', password='p')`                    |
| Private wiki      | `mwclient.Site('wiki.org', do_init=False); site.login(...)`       |
| Custom user-agent | `mwclient.Site('wiki.org', clients_useragent='MyTool/1.0')`       |
| HTTP Basic auth   | `mwclient.Site('wiki.org', httpauth=('user', 'pass'))`            |
| SSL client cert   | `mwclient.Site('wiki.org', client_certificate='cert.pem')`        |
| Reuse session     | `mwclient.Site('wiki.org', pool=my_session)`                      |
| Anonymous edits   | `mwclient.Site('wiki.org', force_login=False)`                    |

## Connection setup

### Standard connection

```python
import mwclient

site = mwclient.Site('en.wikipedia.org')
```

The host parameter takes hostname only — no scheme, no path. The library constructs the URL as `{scheme}://{host}{path}api{ext}` internally.

### Non-standard wiki paths

```python
# Wiki at /wiki/ instead of /w/
site = mwclient.Site('mywiki.example.org', path='/wiki/')

# Custom extension
site = mwclient.Site('mywiki.example.org', ext='.php5')

# HTTP instead of HTTPS
site = mwclient.Site('mywiki.example.org', scheme='http')
```

### Connection options

```python
site = mwclient.Site(
    'en.wikipedia.org',
    max_retries=10,           # Default 25
    retry_timeout=15,         # Default 30 seconds per level
    max_lag=5,                # Default 3 seconds
    compress=True,            # Request gzip (default)
    clients_useragent='MyBot/1.0 (contact@example.org)',
)
```

### Using a pre-existing session

```python
import requests

session = requests.Session()
session.proxies = {'https': 'http://proxy:8080'}
session.verify = '/path/to/ca-bundle.crt'

site = mwclient.Site('en.wikipedia.org', pool=session)
```

## Authentication methods

### Bot passwords (recommended for bots)

```python
site = mwclient.Site('en.wikipedia.org')
site.login('MyBot@BotPasswordName', 'actual_password_here')
```

Bot passwords are created in Special:BotPasswords on the wiki. The format is `Username@BotName`. After login, `site.logged_in` is `True` and `site.username` reflects the actual username.

The `login()` method handles:

-   MW 1.27+ login token flow automatically
-   Throttle retries (waits and retries on `"Throttled"` response)
-   Credential storage for automatic re-login on session recovery

### OAuth 1 (recommended for Wikimedia tools)

```python
site = mwclient.Site(
    'en.wikipedia.org',
    consumer_token='your_consumer_token',
    consumer_secret='your_consumer_secret',
    access_token='your_access_token',
    access_secret='your_access_secret',
)
```

OAuth credentials are "owner-only consumer" tokens — no redirect flow needed. Invalid credentials raise `OAuthAuthorizationError` during `site_init()`. No `login()` call is needed.

### clientlogin (MW 1.27+ interactive login)

```python
site = mwclient.Site('en.wikipedia.org')
result = site.clientlogin(username='MyUser', password='MyPassword')
# Returns True on PASS
# Raises LoginError on FAIL
# Returns dict on UI/REDIRECT (multi-step flow)
```

### HTTP Basic authentication

```python
site = mwclient.Site(
    'private.wiki.org',
    httpauth=('username', 'password'),
)
```

### Custom HTTP auth

```python
from requests.auth import HTTPDigestAuth

site = mwclient.Site(
    'wiki.org',
    httpauth=HTTPDigestAuth('user', 'pass'),
)
```

### SSL client certificate

```python
# Single PEM file
site = mwclient.Site('wiki.org', client_certificate='client.pem')

# Separate cert and key
site = mwclient.Site('wiki.org', client_certificate=('client.crt', 'client.key'))
```

## Private wikis

Private wikis deny API access to unauthenticated users. Use `do_init=False` to defer the initial API call, authenticate, then proceed:

```python
site = mwclient.Site('private.wiki.org', do_init=False)
site.login('admin', 'secret')
# site_init() runs automatically inside login()
page = site.pages['Main Page']
print(page.text())
```

Without `do_init=False`, the constructor's `site_init()` call would fail with `readapidenied` (which is silently swallowed, leaving `site.initialized = False`).

## Token management

Tokens are cached in `site.tokens` and cleared on every `site_init()` call:

```python
# Force-refresh a stale token
token = site.get_token('csrf', force=True)
```

Token types: `'csrf'` (most operations), `'login'` (authentication), `'email'` (sending email). For MW >= 1.24, most token types are remapped to `'csrf'` automatically.

## Edge cases and gotchas

-   **`force_login=True` (default)**: Write operations raise `AssertUserFailedError` if not logged in. Set `force_login=False` explicitly for anonymous edits.
-   **User-agent requirement**: Wikimedia requires a descriptive user-agent. Use `clients_useragent` to prepend your tool name.
-   **Session persistence**: The `requests.Session` stored in `site.connection` persists cookies across requests. Reusing the same `Site` object maintains login state.
-   **OAuth errors surface late**: Invalid OAuth credentials don't fail at construction — they fail during `site_init()` with `OAuthAuthorizationError`.

## See also

-   [02-page-operations.md](02-page-operations.md) — Reading and writing pages
-   [06-error-handling.md](06-error-handling.md) — Login errors and retry logic
-   [../references/reference.md](../references/reference.md) — Full Site constructor signature
