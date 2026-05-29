---
name: mwclient-file-operations
description: Uploading and downloading files and images with mwclient — site.upload(), image.download(), chunked uploads, stash workflow, file metadata, image history.
applies_to:
    - "upload"
    - "download"
    - "Image"
    - "imageinfo"
    - "file"
    - "chunked"
    - "stash"
    - "filekey"
---

# File Operations

## When to use this file

When the user needs to upload files to a wiki, download images, get file metadata, or work with file revision history.

## Mental model

Files on MediaWiki are pages in namespace 6 (File:). The `Image` class extends `Page` with file-specific methods. Uploads go through `site.upload()` with three modes: direct file, URL fetch, or two-phase stash. Large files are automatically chunked. Downloads stream through `image.download()`.

## Quick reference

| Task              | Code                                                  |
| ----------------- | ----------------------------------------------------- |
| Get image handle  | `image = site.images['File:Name.jpg']`                |
| Upload local file | `site.upload(open('f.jpg','rb'), 'Name.jpg')`         |
| Upload from URL   | `site.upload(url='https://...', filename='Name.jpg')` |
| Upload, overwrite | `site.upload(f, 'Name.jpg', ignore=True)`             |
| Stash upload      | `site.upload(f, 'Name.jpg', stash=True)`              |
| Download to file  | `image.download(open('out.jpg','wb'))`                |
| Download to bytes | `data = image.download()`                             |
| Get file metadata | `image.imageinfo`                                     |
| File history      | `image.imagehistory()`                                |
| Pages using file  | `image.imageusage()`                                  |
| Duplicate files   | `image.duplicatefiles()`                              |

## Working with Image objects

### Get an Image

```python
image = site.images['Example.jpg']  # With or without "File:" prefix
print(image.exists)           # True if file exists locally
print(image.imageinfo)        # Dict with url, size, sha1, mime, etc.
print(image.imagerepository)  # 'local', 'shared', or ''
```

### File metadata

```python
info = image.imageinfo
print(f"URL:  {info['url']}")
print(f"Size: {info['size']} bytes")
print(f"MIME: {info['mime']}")
print(f"SHA1: {info['sha1']}")
print(f"Width: {info['width']}")
print(f"Height: {info['height']}")
print(f"Timestamp: {info['timestamp']}")
print(f"User: {info['user']}")
print(f"Comment: {info.get('comment', '')}")
```

### File history

```python
for rev in image.imagehistory():
    print(rev.get('timestamp'), rev.get('user'), rev.get('url'))
```

### Pages using a file

```python
for page in image.imageusage(max_items=20):
    print(page.name)
```

### Duplicate files

```python
for dup in image.duplicatefiles():
    print(dup)
```

### Shared repository files

Files from shared repositories (e.g., Wikimedia Commons) have `image.exists = False` on the local wiki but `image.imageinfo` is populated. Don't rely on `exists` to check file availability — check `imageinfo` instead:

```python
image = site.images['Commons_file.jpg']
if image.imageinfo:
    print("File is available (may be from shared repository)")
else:
    print("File not found anywhere")
```

## Downloading files

### Stream to disk (recommended for all files)

```python
image = site.images['Example.jpg']
with open('downloaded.jpg', 'wb') as f:
    image.download(f)
```

Streams in 1024-byte chunks — memory-efficient for any file size.

### Load into memory (small files only)

```python
data = image.download()  # Returns bytes
```

For large files, this loads the entire file into memory. Prefer streaming.

## Uploading files

### Direct file upload

```python
with open('photo.jpg', 'rb') as f:
    result = site.upload(f, 'MyPhoto.jpg', description='A photo', comment='Uploading')
```

The `description` parameter sets the file description page content (wikitext). The `comment` parameter is the upload log comment.

### Upload from path string

```python
result = site.upload('photo.jpg', 'MyPhoto.jpg', description='A photo')
```

Passing a string path works — the library opens the file internally.

### Upload from URL

```python
result = site.upload(
    url='https://example.com/image.png',
    filename='RemoteImage.png',
    description='Image fetched from example.com',
)
```

The wiki server fetches the file from the URL.

### Overwrite existing file

```python
with open('updated.jpg', 'rb') as f:
    site.upload(f, 'ExistingFile.jpg', description='Updated version', ignore=True)
```

Without `ignore=True`, uploading to an existing filename raises `FileExists`.

### Chunked upload (automatic)

Files larger than `site.chunk_size` (default 1 MiB) are automatically uploaded in chunks. No extra code needed — just upload normally:

```python
with open('large_video.mp4', 'rb') as f:
    site.upload(f, 'Video.mp4', description='A video')
# Automatically uses chunked upload if file > 1 MiB
```

### Two-phase stash upload

For more control, stash the file first, then publish:

```python
# Phase 1: stash
with open('image.jpg', 'rb') as f:
    result = site.upload(f, 'Image.jpg', stash=True)
filekey = result['filekey']

# Phase 2: publish
site.upload(filename='Image.jpg', filekey=filekey, comment='Publishing')
```

This is useful for validating file metadata before committing the upload.

### Asynchronous upload

```python
with open('huge_file.zip', 'rb') as f:
    site.upload(f, 'Archive.zip', asynchronous=True, description='Large archive')
```

The server processes the upload in the background.

## Upload errors

```python
from mwclient import errors

try:
    with open('image.jpg', 'rb') as f:
        site.upload(f, 'Image.jpg', description='Photo')
except errors.FileExists:
    print("File already exists — use ignore=True to overwrite")
except errors.InsufficientPermission:
    print("You don't have permission to upload")
except errors.APIError as e:
    print(f"Upload failed: {e.code} — {e.info}")
```

## Edge cases and gotchas

-   **`image.exists` vs shared repos**: `exists` only checks the local wiki. Commons files show `exists=False` but have valid `imageinfo`. Use `imageinfo` to check availability.
-   **`ignore=False` (default)**: Raises `FileExists` if the target filename exists. This is a client-side check — MediaWiki itself returns a warning, not an error.
-   **Large file memory**: `image.download()` without a destination loads the entire file into memory. Always use streaming for files over a few MB.
-   **Filename convention**: MediaWiki file names are case-sensitive after the first character. `File:Example.jpg` and `File:example.jpg` may be different files.
-   **Upload requires `upload` right**: The bot/user must have the `upload` permission. Check with `site.rights`.

## See also

-   [02-page-operations.md](02-page-operations.md) — Page-level operations (Image extends Page)
-   [06-error-handling.md](06-error-handling.md) — Upload error handling
-   [../references/reference.md](../references/reference.md) — Full Image and upload signatures
