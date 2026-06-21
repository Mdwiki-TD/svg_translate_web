# Image/File Operations

## Overview

This reference covers the `Image` class and file upload functionality in mwclient. The `Image` class extends `Page` to handle file metadata, history, usage, and download operations. Uploading is handled via `Site.upload()`.

**Key Files:**

-   `mwclient/image.py` - Image class implementation
-   `mwclient/client.py` - Site.upload() method
-   `mwclient/util.py` - Chunked upload utilities

## The Image Class

`Image` extends `Page` and is used for files in namespace 6 (`File:`). When any listing returns a page in namespace 6, the listing machinery dispatches to `Image` rather than plain `Page`.

```
Page
└── Image (adds file-specific methods and properties)
```

### Obtaining an Image Object

```python
# Via site.images (namespace prefix omitted)
image = site.images['Example.jpg']

# Via site.pages (namespace prefix required)
image = site.pages['File:Example.jpg']
```

> **Note:** `Image.exists` is `True` only if the file exists **locally** on the wiki. Files from shared repositories (e.g., Wikimedia Commons) return `False`. To test availability from any repository, check `image.imageinfo != {}`.

## Image Properties

At construction, `Image` requests `imageinfo` data from the API. The result is stored in:

| Attribute         | Type   | Description                                          |
| ----------------- | ------ | ---------------------------------------------------- |
| `imagerepository` | `str`  | Where file is stored: `'local'`, `'shared'`, or `''` |
| `imageinfo`       | `dict` | Metadata for the most recent file revision           |

### imageinfo Structure

```python
{
    'comment':   'Uploaded new version',
    'height':    178,
    'metadata':  [{'name': 'MEDIAWIKI_EXIF_VERSION', 'value': 1}],
    'mime':      'image/jpeg',
    'sha1':      'd01b79a6781c72ac9bfff93e5e2cfbeef4efc840',
    'size':      9022,
    'timestamp': '2010-03-14T17:20:20Z',
    'url':       'https://upload.wikimedia.org/...Example.jpg',
    'user':      'SomeUser',
    'width':     172
}
```

The `url` field is used by `download()` method.

## Image Methods

### imagehistory()

Returns a `PageProperty` iterator yielding one dict per historical revision.

```python
for rev in image.imagehistory():
    print(rev['timestamp'], rev['user'], rev['sha1'])
```

### imageusage()

Returns a `List` (or `GeneratorList` when `generator=True`) of pages that embed or link to the file.

```python
for page in image.imageusage():
    print(page.name)  # Page objects

for title in image.imageusage(generator=False):
    print(title)      # Title strings
```

| Parameter        | Type       | Default | Description                                      |
| ---------------- | ---------- | ------- | ------------------------------------------------ |
| `namespace`      | `int/None` | `None`  | Restrict to namespace                            |
| `filterredir`    | `str`      | `'all'` | Filter: `'all'`, `'redirects'`, `'nonredirects'` |
| `redirect`       | `bool`     | `False` | Follow redirect links to file                    |
| `max_items`      | `int/None` | `None`  | Hard cap on results                              |
| `api_chunk_size` | `int/None` | `None`  | Results per API call                             |
| `generator`      | `bool`     | `True`  | Return `Page` objects or title strings           |

### duplicatefiles()

Returns a `PageProperty` iterator listing other files with the same SHA-1 hash.

```python
for dup in image.duplicatefiles():
    print(dup['name'])
```

| Parameter        | Type       | Default | Description          |
| ---------------- | ---------- | ------- | -------------------- |
| `max_items`      | `int/None` | `None`  | Hard cap on results  |
| `api_chunk_size` | `int/None` | `None`  | Results per API call |

### download(destination=None)

Downloads the full-resolution file.

```python
# Load into memory
data = image.download()

# Stream to file (preferred for large files)
with open('local_copy.jpg', 'wb') as fd:
    image.download(fd)
```

| Call Form            | Return  | Behavior                                               |
| -------------------- | ------- | ------------------------------------------------------ |
| `image.download()`   | `bytes` | Entire file loaded into memory                         |
| `image.download(fd)` | `None`  | Streams content to file descriptor in 1024-byte chunks |

## Uploading Files

Uploading is done via `Site.upload()`, not the `Image` class.

```python
site.upload(
    file=None,
    filename='',
    description='',
    comment='',
    ignore=False,
    url=None,
    filekey=None,
    stash=False,
    asynchronous=False
)
```

### Upload Parameters

| Parameter      | Type            | Description                                              |
| -------------- | --------------- | -------------------------------------------------------- |
| `file`         | `BinaryIO/None` | File object to upload                                    |
| `filename`     | `str`           | Destination filename (without `File:` prefix)            |
| `description`  | `str`           | File description (used as initial wikitext)              |
| `comment`      | `str`           | Edit summary for upload log                              |
| `ignore`       | `bool`          | Proceed even if warnings exist (duplicate/existing file) |
| `url`          | `str/None`      | Fetch and upload from URL (server-side fetch)            |
| `filekey`      | `str/None`      | Key of previously stashed upload to finalize             |
| `stash`        | `bool`          | Stash file instead of publishing; returns `filekey`      |
| `asynchronous` | `bool`          | Perform finalization asynchronously                      |

### Upload Modes

1. **Direct upload** - Small files uploaded in single request
2. **Chunked upload** - Large files (> chunk_size, default 1 MiB) uploaded in chunks
3. **Stash mode** - Upload bytes without publishing (two-phase workflow)
4. **URL upload** - Server fetches from provided URL
5. **From stash** - Finalize previously stashed upload

### Upload Examples

**Basic upload:**

```python
with open('diagram.png', 'rb') as f:
    result = site.upload(
        file=f,
        filename='MyDiagram.png',
        description='Diagram showing system architecture',
        comment='Initial upload',
        ignore=True
    )
assert result['result'] == 'Success'
```

**Two-phase stash workflow:**

```python
# Phase 1: Upload to stash
resp = site.upload(
    file=open('photo.jpg', 'rb'),
    filename='photo.jpg',
    description='A photo',
    stash=True
)
filekey = resp['filekey']

# Phase 2: Publish from stash
site.upload(filekey=filekey, filename='photo.jpg')
```

**Upload from URL:**

```python
site.upload(
    url='https://example.com/image.jpg',
    filename='RemoteImage.jpg',
    description='Downloaded from remote source'
)
```

## Error Handling

| Error                    | When Raised                       |
| ------------------------ | --------------------------------- |
| `InsufficientPermission` | User lacks `upload` right         |
| `FileExists`             | File exists and `ignore=False`    |
| `APIError`               | General API failure during upload |

**FileExists example:**

```python
from mwclient import errors

try:
    site.upload(file=f, filename='Existing.jpg')
except errors.FileExists as e:
    print(f'File {e.file_name} exists')
    # Retry with ignore=True to overwrite
    site.upload(file=f, filename='Existing.jpg', ignore=True)
```

## Common Patterns

### Download and process an image

```python
image = site.images['Example.jpg']
if image.imageinfo:
    print(f"Size: {image.imageinfo['width']}x{image.imageinfo['height']}")

    # Download
    with open('local.jpg', 'wb') as f:
        image.download(f)
```

### Check file usage across wiki

```python
image = site.images['Template.png']
for page in image.imageusage():
    print(f"Used on: {page.name}")
```

### Upload with progress check

```python
import os

file_path = 'large_file.zip'
file_size = os.path.getsize(file_path)

with open(file_path, 'rb') as f:
    # Files > chunk_size (1 MiB) will use chunked upload
    result = site.upload(
        file=f,
        filename='LargeFile.zip',
        description='Large file upload',
        comment=f'Uploading {file_size} bytes'
    )
```

### Get file history

```python
image = site.images['Document.pdf']
for rev in image.imagehistory():
    print(f"{rev['timestamp']} - {rev['user']} - {rev.get('comment', '')}")
```

### Check for duplicates

```python
image = site.images['Photo.jpg']
duplicates = list(image.duplicatefiles())
if duplicates:
    print(f"Found {len(duplicates)} duplicate(s)")
```

## Namespace and Object Dispatch

Access patterns and their resulting types:

| Access Pattern            | Returns    | Notes                            |
| ------------------------- | ---------- | -------------------------------- |
| `site.images['Name']`     | `Image`    | Prepends `File:` prefix          |
| `site.pages['File:Name']` | `Image`    | Namespace detected from prefix   |
| `site.pages['Name']`      | `Page`     | Unless name has namespace prefix |
| `site.categories['Name']` | `Category` | Prepends `Category:` prefix      |

When iterating over page lists with `generator=True`, the namespace field determines the class:

-   `ns=6` → `Image`
-   `ns=14` → `Category`
-   Other → `Page`
