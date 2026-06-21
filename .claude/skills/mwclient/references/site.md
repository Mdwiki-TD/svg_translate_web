# Site Operations

## Overview

This reference covers the `Site` class in mwclient, the central class for interacting with MediaWiki instances. Every operation — reading pages, making edits, uploading files, or querying lists — begins with constructing a `Site` instance.

**Key Files:**

-   `mwclient/client.py` - Site class implementation
-   `mwclient/__init__.py` - Re-exports `Site`

## The Site Class

`Site` manages HTTP communication, bootstraps site metadata, exposes page accessors, and provides the core API methods.

```python
import mwclient
site = mwclient.Site('en.wikipedia.org')
```

## Constructor

```python
Site(
    host,                          # Required: hostname without scheme
    path='/w/',                    # Script path (must end with /)
    ext='.php',                    # File extension for API scripts
    pool=None,                     # Pre-existing requests.Session
    retry_timeout=30,              # Seconds to sleep per past retry
    max_retries=25,                # Max retry attempts
    wait_callback=None,            # Called on each retry
    clients_useragent=None,        # Prepended to user agent
    max_lag=3,                     # maxlag for index.php calls
    compress=True,                 # Request gzip compression
    force_login=True,              # Require auth before editing
    do_init=True,                  # Run site_init() during construction
    httpauth=None,                 # HTTP Basic auth tuple or AuthBase
    connection_options=None,       # Extra kwargs for requests
    consumer_token=None,           # OAuth1 consumer key
    consumer_secret=None,          # OAuth1 consumer secret
    access_token=None,             # OAuth1 access token
    access_secret=None,            # OAuth1 access secret
    client_certificate=None,       # Path to PEM or (cert, key) tuple
    custom_headers=None,           # Additional headers
    scheme='https',                # 'http' or 'https'
    reqs=None                      # Deprecated: use connection_options
)
```

## Key Instance Attributes

After `site_init()` completes:

| Attribute     | Type             | Description                                 |
| ------------- | ---------------- | ------------------------------------------- |
| `host`        | `str`            | Hostname as passed to constructor           |
| `path`        | `str`            | Script path (e.g., `/w/`)                   |
| `scheme`      | `str`            | `'https'` or `'http'`                       |
| `version`     | `tuple`          | MediaWiki version, e.g., `(1, 39, 5)`       |
| `namespaces`  | `dict[int, str]` | Namespace ID → name mapping                 |
| `site`        | `dict`           | Raw `query.general` siteinfo                |
| `username`    | `str`            | Currently authenticated user                |
| `groups`      | `list[str]`      | User's groups                               |
| `rights`      | `list[str]`      | User's rights                               |
| `blocked`     | `bool/tuple`     | `False` or `(blocked_by, reason)`           |
| `hasmsg`      | `bool`           | Unread talk page messages?                  |
| `logged_in`   | `bool`           | `True` if not anonymous                     |
| `tokens`      | `dict[str, str]` | Cached API tokens                           |
| `initialized` | `bool`           | `True` after first successful `site_init()` |
| `force_login` | `bool`           | Controls unauthenticated edit gating        |
| `pages`       | `PageList`       | Entry point for all pages                   |
| `images`      | `PageList`       | Entry point for namespace 6 (File)          |
| `categories`  | `PageList`       | Entry point for namespace 14 (Category)     |
| `connection`  | `Session`        | Underlying HTTP session                     |
| `chunk_size`  | `int`            | Upload chunk size (default 1 MiB)           |

## Authentication

### OAuth 1

```python
site = mwclient.Site(
    'en.wikipedia.org',
    consumer_token='my_consumer_token',
    consumer_secret='my_consumer_secret',
    access_token='my_access_token',
    access_secret='my_access_secret'
)
```

### HTTP Basic Auth

```python
site = mwclient.Site('mywiki.example.org', httpauth=('user', 'pass'))
```

### clientlogin (Recommended for interactive)

```python
site = mwclient.Site('mywiki.example.org')
site.clientlogin(username='myuser', password='secret')
```

### Legacy login (for bot passwords)

```python
site = mwclient.Site('mywiki.example.org')
site.login(username='myuser', password='botpassword')
```

### SSL Client Certificate

```python
# Single combined PEM
site = mwclient.Site('mywiki.example.org', client_certificate='/path/to/client.pem')

# Separate cert and key
site = mwclient.Site('mywiki.example.org', client_certificate=('client.pem', 'key.pem'))
```

## Core API Methods

### site.get(action, \*\*kwargs)

Shorthand for `api(action, 'GET', ...)`. Use for idempotent read operations.

```python
result = site.get('query', meta='siteinfo')
```

### site.post(action, \*\*kwargs)

Shorthand for `api(action, 'POST', ...)`. Use for write operations.

```python
result = site.post('edit', title='Page', text='Content', token=token)
```

### site.api(action, http_method='POST', \*\*kwargs)

The primary API call method.

```python
result = site.api('query', http_method='GET', meta='userinfo')
```

## Site-Level Listing Methods

### allpages()

Iterate over all pages on the wiki.

```python
for page in site.allpages(namespace=0, filterredir='nonredirects'):
    print(page.name)
```

### search()

Search the wiki.

```python
for page in site.search('python', namespace=0):
    print(page.name)
```

### recentchanges()

Get recent changes.

```python
for change in site.recentchanges(namespace=0, limit=50):
    print(change['title'], change['timestamp'])
```

### usercontributions()

Get contributions by a user.

```python
for contrib in site.usercontributions('Username'):
    print(contrib['title'])
```

### logevents()

Get log events.

```python
for log in site.logevents(logtype='upload'):
    print(log['title'])
```

### allimages(), allcategories(), allusers()

Similar patterns for other list types.

## Token Management

### get_token(type, force=False)

Retrieves and caches API tokens.

```python
csrf_token = site.get_token('csrf')      # For edits
login_token = site.get_token('login')    # For login
email_token = site.get_token('email')    # For email
```

Tokens are cached in `site.tokens` and cleared on `site_init()`.

## Version Checking

### require(major, minor, revision=None)

Check if connected MediaWiki meets minimum version.

```python
if site.require(1, 35, raise_error=False):
    # Use features requiring MW 1.35+
    pass
```

## Page Access

### site.pages

Access any page by title:

```python
page = site.pages['Main Page']
page = site.pages['Template:Infobox']
page = site.pages['Category:Python']
```

### site.images

Access files (namespace 6), prepends `File:` automatically:

```python
image = site.images['Example.jpg']  # Equivalent to site.pages['File:Example.jpg']
```

### site.categories

Access categories (namespace 14), prepends `Category:` automatically:

```python
cat = site.categories['Python']  # Equivalent to site.pages['Category:Python']
```

## Utility Methods

### expandtemplates(text, title=None)

Expands templates in wikitext.

```python
expanded = site.expandtemplates('{{CURRENTYEAR}}')
```

### parse(title=None, text=None, page=None)

Parse wikitext and return HTML.

```python
result = site.parse(text='== Heading ==\nParagraph')
html = result['text']['*']
```

### email(user, subject, text)

Send email to a user.

```python
site.email('TargetUser', subject='Hello', text='Message body')
```

## Error Handling

| Error                     | When Raised                            |
| ------------------------- | -------------------------------------- |
| `MediaWikiVersionError`   | Version parsing fails or below minimum |
| `APIDisabledError`        | API is disabled on target site         |
| `InvalidResponse`         | Server returns non-JSON                |
| `MaximumRetriesExceeded`  | Retry limit exhausted                  |
| `APIError`                | General API error                      |
| `LoginError`              | Login attempt fails                    |
| `OAuthAuthorizationError` | OAuth authentication fails             |
| `InsufficientPermission`  | Operation requires missing permission  |

## Common Patterns

### Connect and authenticate

```python
import mwclient

site = mwclient.Site('en.wikipedia.org')
site.login('Username', 'password')
print(f"Logged in as {site.username}")
print(f"Rights: {site.rights}")
```

### Check if user can perform action

```python
if 'upload' in site.rights:
    # Can upload files
    pass

if 'delete' in site.rights:
    # Can delete pages
    pass
```

### Iterate all pages in namespace

```python
for page in site.allpages(namespace=10, prefix='Infobox'):  # Templates
    print(page.name)
```

### Search with limit

```python
for page in site.search('python', namespace=0, max_items=10):
    print(page.name)
```

### Handle blocked user

```python
if site.blocked:
    blocked_by, reason = site.blocked
    print(f"Blocked by {blocked_by}: {reason}")
```

### Raw API call for custom actions

```python
result = site.get('query', list='allusers', auprop='editcount')
for user in result['query']['allusers']:
    print(user['name'], user['editcount'])
```

## Connection Options

Pass custom options to all requests:

```python
site = mwclient.Site(
    'mywiki.example.org',
    connection_options={
        'timeout': 30,
        'verify': '/path/to/ca-bundle.crt'
    }
)
```
