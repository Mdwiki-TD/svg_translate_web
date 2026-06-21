# Page Operations

## Overview

This reference covers the `Page` class in mwclient, which represents a single wiki page. The `Page` class provides methods for reading content, making edits, and querying page relationships.

**Key Files:**

-   `mwclient/page.py` - Main Page class implementation

## Page Class

The `Page` class is the primary object representing a single wiki page. It holds page metadata (fetched at instantiation) and provides methods for content operations.

### Class Hierarchy

| Class      | Module                | Namespace           |
| ---------- | --------------------- | ------------------- |
| `Page`     | `mwclient/page.py`    | All others          |
| `Image`    | `mwclient/image.py`   | File / Image (ns 6) |
| `Category` | `mwclient/listing.py` | Category (ns 14)    |

`Image` inherits from `Page`. `Category` inherits from both `Page` and `GeneratorList`.

### Instantiating a Page

**Direct construction:**

```python
page = mwclient.page.Page(site, name, info=None, extra_properties=None)
```

| Parameter          | Type               | Description                                        |
| ------------------ | ------------------ | -------------------------------------------------- |
| `site`             | `Site`             | The site the page belongs to                       |
| `name`             | `int`/`str`/`Page` | Page title, page ID, or Page instance to copy      |
| `info`             | `dict`/`None`      | Pre-fetched page info; if `None`, API call is made |
| `extra_properties` | `dict`/`None`      | Additional API properties to fetch                 |

**Via site.pages (typical):**

```python
page = site.pages['Main Page']
image = site.images['Example.jpg']      # namespace 6
category = site.categories['Python']     # namespace 14
```

## Page Properties

After construction, these attributes are populated from the API:

| Attribute          | Type                      | Description                                     |
| ------------------ | ------------------------- | ----------------------------------------------- |
| `name`             | `str`                     | Full title including namespace prefix           |
| `namespace`        | `int`                     | Integer namespace ID; 0 = main                  |
| `exists`           | `bool`                    | `False` if the page does not exist              |
| `revision`         | `int`                     | Latest revision ID; 0 if new                    |
| `pageid`           | `int`/`None`              | MediaWiki page ID; `None` if page doesn't exist |
| `protection`       | `dict`                    | Maps action string → `(level, expiry)` tuple    |
| `redirect`         | `bool`                    | `True` if the page is a redirect                |
| `length`           | `int`/`None`              | Page size in bytes                              |
| `touched`          | `time.struct_time`/`None` | Timestamp of last cache invalidation            |
| `contentmodel`     | `str`/`None`              | e.g. `'wikitext'`, `'json'`                     |
| `pagelanguage`     | `str`/`None`              | Language code e.g. `'en'`                       |
| `restrictiontypes` | `list`/`None`             | Which actions can be protected                  |

**Derived title properties:**

-   `page_title` - Title without namespace prefix
-   `base_title` - Top-level title before first `/` (no namespace)
-   `base_name` - Top-level title before first `/` (with namespace)

## Reading Page Content

### page.text()

Primary method for retrieving a page's wikitext content.

```python
text = page.text(
    section: Union[int, str, None] = None,
    expandtemplates: bool = False,
    cache: bool = True,
    slot: str = 'main'
) -> str
```

| Parameter         | Type               | Default  | Description                               |
| ----------------- | ------------------ | -------- | ----------------------------------------- |
| `section`         | `int`/`str`/`None` | `None`   | Section number or `T-<number>` identifier |
| `expandtemplates` | `bool`             | `False`  | If `True`, expands all templates          |
| `cache`           | `bool`             | `True`   | Use instance-level `_textcache`           |
| `slot`            | `str`              | `'main'` | Content slot (MediaWiki ≥ 1.32)           |

**Behavior:**

-   Checks `can('read')` permission first; raises `InsufficientPermission` if lacking
-   Returns empty string `''` if page doesn't exist
-   Uses in-memory cache keyed by `(section, expandtemplates)`
-   Updates `page.last_rev_time` with revision timestamp

### page.revisions()

Returns a `RevisionsIterator` for paginating through revision history.

```python
revs = page.revisions(
    startid=None, endid=None,
    start=None, end=None,
    dir='older',
    user=None, excludeuser=None,
    limit=None,                    # Deprecated
    prop='ids|timestamp|flags|comment|user',
    expandtemplates=False,
    section=None,
    diffto=None,
    slots=None,
    uselang=None,
    max_items=None,
    api_chunk_size=50
) -> RevisionsIterator
```

Yields dicts containing fields specified by `prop`. Add `content` to `prop` to get wikitext.

### Redirect Resolution

```python
page.redirects_to() -> Optional[Page]   # Returns target Page or None
page.resolve_redirect() -> Page         # Returns target or self
```

Example:

```python
page = site.pages['WP:AN']              # might be a redirect
canonical = page.resolve_redirect()     # returns target or page itself
text = canonical.text()
```

## Editing Pages

### Edit Methods

| Method      | Parameters                           | API Action                | Required Permission |
| ----------- | ------------------------------------ | ------------------------- | ------------------- |
| `edit()`    | `text, summary, minor, bot, section` | `edit`                    | `can('edit')`       |
| `append()`  | `text, summary, minor, bot, section` | `edit`                    | `can('edit')`       |
| `prepend()` | `text, summary, minor, bot, section` | `edit`                    | `can('edit')`       |
| `save()`    | same as `edit()`                     | `edit`                    | `can('edit')`       |
| `touch()`   | _(none)_                             | `edit` (via `append('')`) | `can('edit')`       |

**Common edit parameters:**

| Parameter | Type            | Default      | Effect                           |
| --------- | --------------- | ------------ | -------------------------------- |
| `text`    | `str`           | _(required)_ | Page content or delta            |
| `summary` | `str`           | `''`         | Edit summary                     |
| `minor`   | `bool`          | `False`      | Mark as minor edit               |
| `bot`     | `bool`          | `True`       | Mark as bot edit                 |
| `section` | `Optional[str]` | `None`       | Target section number or `'new'` |

Example:

```python
page.edit('New page content', summary='Updated content')
page.append('\nNew line', summary='Added line')
page.prepend('Header\n', summary='Added header')
```

### Managing Pages

```python
page.move(new_title, reason='', move_talk=True, no_redirect=False,
          move_subpages=False, ignore_warnings=False)
page.delete(reason='', watch=False, unwatch=False, oldimage=None)
page.purge()  # Forces MediaWiki to re-render the page
```

## Page Listings

Methods that return iterable objects for page relationships:

| Method         | Has `generator` param | Default Mode          | Non-generator yields    |
| -------------- | --------------------- | --------------------- | ----------------------- |
| `backlinks()`  | Yes                   | `generator=True`      | title string            |
| `categories()` | Yes                   | `generator=True`      | title string            |
| `embeddedin()` | Yes                   | `generator=True`      | title string            |
| `extlinks()`   | No                    | always `PageProperty` | URL string              |
| `images()`     | Yes                   | `generator=True`      | title string            |
| `iwlinks()`    | No                    | always `PageProperty` | `(prefix, title)` tuple |
| `langlinks()`  | No                    | always `PageProperty` | `(lang, title)` tuple   |
| `links()`      | Yes                   | `generator=True`      | title string            |
| `templates()`  | Yes                   | `generator=True`      | title string            |

**Generator mode** (`generator=True`): yields `Page`/`Image`/`Category` objects
**Non-generator mode** (`generator=False`): yields raw strings or tuples

Example:

```python
# Get backlinks as Page objects
for linking_page in page.backlinks():
    print(linking_page.name)

# Get categories as title strings
for cat in page.categories(generator=False):
    print(cat)

# Get interwiki links
for prefix, title in page.iwlinks():
    print(f'{prefix}:{title}')
```

## Permission Checking

```python
page.can(action) -> bool
```

Checks whether the current user has permission to perform an action on the page.

```python
if page.can('edit'):
    page.edit('New content')
if page.can('move'):
    page.move('New Title')
if page.can('delete'):
    page.delete()
```

## Error Handling

Common errors when working with pages:

| Error                    | When Raised                          |
| ------------------------ | ------------------------------------ |
| `InsufficientPermission` | User lacks permission for action     |
| `ProtectedPageError`     | Page is protected against action     |
| `EditError`              | Edit failed (edit conflict, etc.)    |
| `AssertUserFailedError`  | Not logged in and `force_login=True` |
| `UserBlocked`            | User account is blocked              |
| `InvalidPageTitle`       | Title contains illegal characters    |

## Token Acquisition

```python
page.get_token(type, force=False)
```

Delegates to `site.get_token()`. Used internally for edit, move, and delete operations.

## Common Patterns

### Read, Modify, Save

```python
page = site.pages['My Page']
text = page.text()
new_text = text.replace('old', 'new')
page.edit(new_text, summary='Replaced old with new')
```

### Check if page exists before editing

```python
page = site.pages['New Page']
if not page.exists:
    page.edit('Initial content', summary='Created page')
```

### Handle redirects

```python
page = site.pages['Shortcut']
if page.redirect:
    page = page.resolve_redirect()
text = page.text()
```

### Iterate backlinks with filter

```python
for p in page.backlinks(namespace=0, filterredir='nonredirects'):
    print(p.name)
```

### Get all revisions by a user

```python
for rev in page.revisions(user='SomeUser', dir='older'):
    print(rev['timestamp'], rev['comment'])
```
