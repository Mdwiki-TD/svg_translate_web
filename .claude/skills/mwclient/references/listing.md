# Listing and Pagination

## Overview

This reference covers the listing infrastructure in mwclient, which provides lazy, paginated iteration over MediaWiki API query results. All listing methods return iterator objects that fetch data in chunks as needed.

**Key Files:**

-   `mwclient/listing.py` - List, GeneratorList, PageList, PageProperty classes
-   `mwclient/util.py` - handle_limit utility

## Class Hierarchy

All iterator types descend from `List`:

```
List (base)
├── GeneratorList (yields Page/Image/Category objects)
├── PageList (supports __getitem__ access)
│   └── Category (also inherits from Page)
├── PageProperty (prop-based queries)
│   └── RevisionsIterator
└── NestedList (for nested responses)
```

## The List Base Class

`List` is the engine behind all lazy iteration. It holds state for a single paginated query and drives chunk loading on demand.

### Construction Parameters

| Parameter        | Type             | Description                                    |
| ---------------- | ---------------- | ---------------------------------------------- |
| `site`           | `Site`           | The site to query                              |
| `list_name`      | `str`            | MediaWiki list name (e.g., `'allpages'`)       |
| `prefix`         | `str`            | Two-letter API parameter prefix (e.g., `'ap'`) |
| `api_chunk_size` | `int/None`       | Items requested per API call                   |
| `max_items`      | `int/None`       | Total items to yield before stopping           |
| `return_values`  | `str/tuple/None` | Field(s) to extract from each dict             |
| `limit`          | `int/None`       | **Deprecated.** Alias for `api_chunk_size`     |

### api_chunk_size vs max_items

| Parameter        | Scope           | Effect                               |
| ---------------- | --------------- | ------------------------------------ |
| `api_chunk_size` | Per API request | Sets `{prefix}limit` in request      |
| `max_items`      | Total iteration | Stops yielding after this many items |

Examples:

-   `max_items=2, api_chunk_size=1`: Two API calls, one item per call
-   `max_items=2` (no chunk size): Single call returning both items
-   `api_chunk_size=2` (no max): All items, two per call

### return_values

Controls what fields are yielded from each result dict:

| `return_values`   | Yield Type | Example                                  |
| ----------------- | ---------- | ---------------------------------------- |
| `None` (default)  | `dict`     | `{'pageid': 1, 'ns': 0, 'title': 'Foo'}` |
| `'title'`         | scalar     | `'Foo'`                                  |
| `('title', 'ns')` | `tuple`    | `('Foo', 0)`                             |

## GeneratorList

`GeneratorList` extends `List` to yield typed page objects instead of raw dicts.

### Namespace Dispatch

When iterating, `GeneratorList.__next__()` inspects the `ns` field and instantiates the appropriate class:

| Namespace ID | Returns    |
| ------------ | ---------- |
| `14`         | `Category` |
| `6`          | `Image`    |
| Other        | `Page`     |

### Generator Mode Features

-   Renames limit parameter: `{prefix}limit` → `g{prefix}limit` (e.g., `aplimit` → `gaplimit`)
-   Sets `generator='generator'` for API calls
-   Adds `prop=info|imageinfo` and `inprop=protection` to fetch metadata

## PageList

`PageList` is the type behind `site.pages`, `site.images`, and `site.categories`. It supports both iteration and direct item access via `__getitem__`.

### Namespace Guessing

When accessing via `site.pages['Name']`, `PageList` guesses the namespace:

```python
page = site.pages['Template:Infobox']  # Detects namespace 10
page = site.pages['File:Image.jpg']     # Detects namespace 6, returns Image
page = site.pages['Category:Python']    # Detects namespace 14, returns Category
```

## PageProperty and RevisionsIterator

`PageProperty` is used for per-page API property queries (e.g., `revisions`, `extlinks`). Unlike `List`, it is bound to a specific `Page` object.

### PageProperty Features

-   Sets `self.generator = 'prop'`
-   Searches `data['query']['pages']` to find the specific page by title
-   Iterates only over that page's property array

### RevisionsIterator

Extends `PageProperty` with special handling for `rvstartid` vs `rvstart` conflict resolution.

## Listing Methods on Site

Site-level listing methods return `List` or `GeneratorList` instances:

```python
# All pages
for page in site.allpages(namespace=0, filterredir='nonredirects'):
    print(page.name)

# Search results
for page in site.search('query', namespace=0):
    print(page.name)

# Recent changes
for change in site.recentchanges(namespace=0):
    print(change['title'])

# User contributions
for contrib in site.usercontributions('Username'):
    print(contrib['title'])

# Log events
for log in site.logevents(logtype='upload'):
    print(log['title'])

# All images/categories/users
for image in site.allimages():
    print(image.name)
for cat in site.allcategories():
    print(cat.name)
```

## Listing Methods on Page

Page-level listing methods that return `GeneratorList` or `List`:

```python
page = site.pages['Main Page']

# Backlinks (pages linking here)
for p in page.backlinks():
    print(p.name)

# Categories this page belongs to
for cat in page.categories():
    print(cat.name)

# Pages that embed/transclude this page
for p in page.embeddedin():
    print(p.name)

# External links from this page
for url in page.extlinks():
    print(url)

# Images embedded in this page
for img in page.images():
    print(img.name)

# Interwiki links
for prefix, title in page.iwlinks():
    print(f'{prefix}:{title}')

# Language links
for lang, title in page.langlinks():
    print(f'{lang}:{title}')

# Internal links
for p in page.links():
    print(p.name)

# Templates transcluded
for t in page.templates():
    print(t.name)

# Revision history
for rev in page.revisions():
    print(rev['timestamp'], rev['user'])
```

## The generator Parameter

Most listing methods accept a `generator` parameter:

| Mode                       | Return Type                             | Yields                            |
| -------------------------- | --------------------------------------- | --------------------------------- |
| `generator=True` (default) | `GeneratorList`/`PagePropertyGenerator` | `Page`/`Image`/`Category` objects |
| `generator=False`          | `List`/`PageProperty`                   | Raw strings, dicts, or tuples     |

Example:

```python
# Generator mode - Page objects
for page in page.backlinks():
    print(page.name)

# Non-generator mode - title strings
for title in page.backlinks(generator=False):
    print(title)
```

## Continuation and Pagination

### New-Style Continuation (MediaWiki ≥ 1.26)

The API returns a top-level `continue` dict with opaque continuation values. `List.load_chunk()` merges these into `self.args`:

```python
# API response: {'continue': {'apcontinue': 'Next_Page', 'continue': '-||'}}
# Next request automatically includes these parameters
```

### Miser Mode Handling

Some wikis return a `continue` token but zero results. The `__next__` loop handles this by calling `load_chunk()` repeatedly until items are found or `self.last` is `True`.

## Common Patterns

### Iterate with limit

```python
# Get first 10 pages only
for page in site.allpages(namespace=0, max_items=10):
    print(page.name)

# Fetch 5 at a time
for page in site.allpages(namespace=0, max_items=100, api_chunk_size=5):
    print(page.name)
```

### Filter by namespace

```python
# Only main namespace (0)
for page in site.allpages(namespace=0):
    print(page.name)

# Multiple namespaces as pipe-separated string
for page in site.recentchanges(namespace='0|1|2'):
    print(page['title'])
```

### Get only titles

```python
# Fast - only fetch titles
for title in site.allpages(namespace=0, return_values='title'):
    print(title)

# Multiple fields as tuple
for title, ns in site.allpages(namespace=0, return_values=('title', 'ns')):
    print(title, ns)
```

### Check if listing has results

```python
pages = list(site.search('unlikely_term_12345', max_items=1))
if pages:
    print("Found results")
else:
    print("No results")
```

### Iterate backlinks with filter

```python
# Only non-redirects in main namespace
for p in page.backlinks(
    namespace=0,
    filterredir='nonredirects'
):
    print(p.name)
```

### Handle generator vs non-generator

```python
# Works with both modes
result = page.links(generator=use_objects)
for item in result:
    if use_objects:
        print(item.name)  # Page object
    else:
        print(item)       # String
```

## Class-to-Role Summary

| Class                   | `generator`   | `result_member` | Primary Use              |
| ----------------------- | ------------- | --------------- | ------------------------ |
| `List`                  | `'list'`      | `list_name`     | Site-level lists         |
| `NestedList`            | `'list'`      | `list_name`     | Nested responses         |
| `GeneratorList`         | `'generator'` | `'pages'`       | Page-level generators    |
| `Category`              | `'generator'` | `'pages'`       | Category members         |
| `PageList`              | `'generator'` | `'pages'`       | Page access              |
| `PageProperty`          | `'prop'`      | prop name       | Page properties          |
| `PagePropertyGenerator` | `'generator'` | `'pages'`       | Page property generators |
| `RevisionsIterator`     | `'prop'`      | `'revisions'`   | Revision history         |
