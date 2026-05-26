---
name: mwclient-examples
description: End-to-end example scripts for common mwclient workflows — authentication, reading, editing, uploading, querying, and error handling.
applies_to:
    - "example"
    - "script"
    - "recipe"
    - "snippet"
---

# mwclient Examples

Copy-paste scripts for common mwclient tasks.

## Table of Contents

1. [Connection and Authentication](#connection-and-authentication)
2. [Reading Pages](#reading-pages)
3. [Editing Pages](#editing-pages)
4. [Page Management](#page-management)
5. [Querying and Iteration](#querying-and-iteration)
6. [File Operations](#file-operations)
7. [Categories and Templates](#categories-and-templates)
8. [Error Handling Patterns](#error-handling-patterns)
9. [Advanced Patterns](#advanced-patterns)

---

## Connection and Authentication

### Public wiki (read-only)

```python
import mwclient

site = mwclient.Site('en.wikipedia.org')
page = site.pages['Main Page']
print(page.exists)  # True
```

### Bot password login

```python
import mwclient

site = mwclient.Site('en.wikipedia.org')
site.login('MyBotName@MyBotPassword', 'bot_password_here')

# Verify login
print(site.logged_in)  # True
print(site.username)    # 'MyBotName'
```

### OAuth 1 (recommended for Wikimedia)

```python
import mwclient

site = mwclient.Site(
    'en.wikipedia.org',
    consumer_token='your_consumer_token',
    consumer_secret='your_consumer_secret',
    access_token='your_access_token',
    access_secret='your_access_secret',
)
# No login() call needed — auth is set during construction
print(site.logged_in)  # True
```

### Private wiki with do_init=False

```python
import mwclient

site = mwclient.Site('private.wiki.example.org', do_init=False)
site.login('admin', 'secret_password')
# site_init() is called automatically by login()
page = site.pages['Main Page']
print(page.text())
```

### Custom user-agent (required by Wikimedia)

```python
site = mwclient.Site(
    'en.wikipedia.org',
    clients_useragent='MyBot/2.0 (https://example.org; admin@example.org)',
)
```

### Using a pre-existing requests.Session

```python
import requests
import mwclient

session = requests.Session()
session.proxies = {'https': 'http://proxy.example.org:8080'}

site = mwclient.Site('en.wikipedia.org', pool=session)
```

---

## Reading Pages

### Read full page text

```python
site = mwclient.Site('en.wikipedia.org')
page = site.pages['Python (programming language)']
text = page.text()
print(text[:500])
```

### Read a specific section

```python
page = site.pages['Wikipedia:Village pump']
text = page.text(section=2)
print(text)
```

### Check if page exists

```python
page = site.pages['Some Nonexistent Page']
if page.exists:
    print(page.text())
else:
    print(f"Page '{page.name}' does not exist")
```

### Read page with expanded templates

```python
page = site.pages['Some Page']
expanded = page.text(expandtemplates=True)
print(expanded)
```

### Read page by ID

```python
import mwclient.page

page = mwclient.page.Page(site, 12345)  # Page ID
print(page.name, page.text()[:100])
```

### Read with cache bypass

```python
text = page.text(cache=False)  # Forces fresh API call
```

---

## Editing Pages

### Simple edit

```python
site = mwclient.Site('en.wikipedia.org')
site.login('MyBot', 'bot_password')

page = site.pages['User:MyBot/Sandbox']
page.save('Hello from mwclient!', summary='Testing mwclient edit')
```

### Edit a specific section

```python
page = site.pages['Talk:Some Article']
page.edit(
    'New section content',
    summary='Updating section 3',
    section='3',
)
```

### Append text to a page

```python
page = site.pages['User:MyBot/Log']
page.append('\n* Task completed at ~~~~~', summary='Logging task')
```

### Prepend text (add header)

```python
page = site.pages['Some Page']
page.prepend('{{Notice|This page is under construction}}\n', summary='Adding notice')
```

### Minor and bot flags

```python
page.save(
    'Fixed typo',
    summary='Fixing typo',
    minor=True,    # Mark as minor edit
    bot=True,      # Mark as bot edit (default True)
)
```

### Null edit (refresh parser cache)

```python
page = site.pages['Template:Some Template']
page.touch()  # No content change, just refreshes cache
```

### Edit with conflict detection

```python
page = site.pages['Some Page']
old_text = page.text()  # This sets basetimestamp for conflict detection

new_text = old_text.replace('old value', 'new value')
page.save(new_text, summary='Updating value')
# If someone edited between text() and save(), EditError is raised
```

---

## Page Management

### Move a page

```python
page = site.pages['Old Title']
page.move('New Title', reason='Renaming for clarity')
```

### Move without leaving redirect

```python
page.move('New Title', reason='Renaming', no_redirect=True)
```

### Delete a page

```python
page = site.pages['Spam Page']
page.delete(reason='Removing spam')
```

### Purge page cache

```python
page = site.pages['Some Template']
page.purge()  # Forces re-render of templates
```

### Check permissions before editing

```python
page = site.pages['Protected Page']
if page.can('edit'):
    page.save('New content', summary='Editing protected page')
else:
    print(f"Cannot edit {page.name} — protection level too high")
```

---

## Querying and Iteration

### List all pages with a prefix

```python
for page in site.allpages(prefix='Python/', namespace=0, max_items=50):
    print(page.name)
```

### Search wiki content

```python
for result in site.search('mwclient mediawiki', namespace=0, max_items=20):
    print(result['title'], result.get('snippet', ''))
```

### Recent changes

```python
for change in site.recentchanges(prop='title|timestamp|user|comment', max_items=20):
    print(f"{change['timestamp']} {change['user']}: {change['title']}")
```

### Get page backlinks

```python
page = site.pages['Python (programming language)']
for link in page.backlinks(max_items=100):
    print(link.name)
```

### Get page revision history

```python
page = site.pages['Some Article']
for rev in page.revisions(prop='ids|timestamp|user|comment', max_items=10):
    print(f"rev {rev['revid']} by {rev.get('user', '?')} at {rev['timestamp']}")
```

### Get latest revision content

```python
page = site.pages['Some Article']
for rev in page.revisions(prop='ids|timestamp|content', api_chunk_size=1):
    print(rev['*'][:200])  # Content is in '*' key
    break  # Only want the latest
```

### Iterate categories

```python
cat = site.categories['Programming languages']
for member in cat.members(max_items=50):
    print(member.name)  # Page objects
```

### Random pages

```python
for page in site.random(namespace=0, max_items=5):
    print(page.name)
```

### User contributions

```python
for contrib in site.usercontributions('SomeUser', max_items=20):
    print(contrib['title'], contrib['timestamp'])
```

### Log events

```python
for event in site.logevents(type='delete', max_items=10):
    print(event['title'], event.get('action'))
```

### External URL usage

```python
for entry in site.exturlusage(query='example.com', max_items=20):
    print(entry['title'], entry.get('url'))
```

---

## File Operations

### Upload a local file

```python
with open('photo.jpg', 'rb') as f:
    site.upload(f, 'MyPhoto.jpg', description='A photo I took', comment='Uploading photo')
```

### Upload from URL

```python
site.upload(
    url='https://example.com/image.png',
    filename='RemoteImage.png',
    description='Image from example.com',
)
```

### Upload with ignore (overwrite)

```python
with open('updated.png', 'rb') as f:
    site.upload(f, 'ExistingFile.png', description='Updated version', ignore=True)
```

### Two-phase stash upload

```python
with open('large_video.mp4', 'rb') as f:
    result = site.upload(f, 'Video.mp4', stash=True)

filekey = result['filekey']
site.upload(filename='Video.mp4', filekey=filekey, comment='Publishing video')
```

### Download a file

```python
image = site.images['Example.jpg']
print(image.imageinfo['url'])  # Direct URL

# Stream to disk
with open('downloaded.jpg', 'wb') as f:
    image.download(f)

# Load into memory (small files only)
data = image.download()
```

### Get file metadata

```python
image = site.images['Example.jpg']
info = image.imageinfo
print(f"Size: {info['size']} bytes")
print(f"MIME: {info['mime']}")
print(f"SHA1: {info['sha1']}")
print(f"URL:  {info['url']}")
```

### File revision history

```python
image = site.images['Example.jpg']
for rev in image.imagehistory():
    print(rev.get('timestamp'), rev.get('user'))
```

### Pages using a file

```python
image = site.images['Example.jpg']
for page in image.imageusage(max_items=20):
    print(page.name)
```

---

## Categories and Templates

### List category members

```python
cat = site.categories['Python']
for member in cat.members(max_items=50):
    print(member.name, '(Category)' if isinstance(member, mwclient.listing.Category) else '')
```

### Get categories on a page

```python
page = site.pages['Python (programming language)']
for cat in page.categories():
    print(cat.name)
```

### Get templates on a page

```python
page = site.pages['Python (programming language)']
for tmpl in page.templates():
    print(tmpl.name)
```

### Find pages that transclude a template

```python
template = site.pages['Template:Infobox programming language']
for page in template.embeddedin(max_items=50):
    print(page.name)
```

### Expand templates

```python
expanded = site.expandtemplates('{{CURRENTTIMESTAMP}}')
print(expanded)

# With parse tree
expanded, tree = site.expandtemplates('{{TemplateName|arg}}', generatexml=True)
```

### Parse wikitext to HTML

```python
result = site.parse('{{TemplateName}}\nSome '''wikitext'''')
print(result.get('text', {}).get('*', ''))
```

---

## Error Handling Patterns

### Catch edit errors

```python
import mwclient
from mwclient import errors

site = mwclient.Site('en.wikipedia.org')
site.login('MyBot', 'password')

page = site.pages['Some Page']
try:
    page.save('New content', summary='Editing')
except errors.ProtectedPageError:
    print(f"Page {page.name} is protected")
except errors.EditError as e:
    print(f"Edit failed: {e}")
except errors.APIError as e:
    print(f"API error: {e.code} — {e.info}")
```

### Handle login failures

```python
try:
    site.login('Bot', 'wrong_password')
except errors.LoginError as e:
    print(f"Login failed: {e.code} — {e.info}")
```

### Handle upload errors

```python
try:
    with open('image.jpg', 'rb') as f:
        site.upload(f, 'Image.jpg', description='Photo')
except errors.FileExists:
    print("File already exists — use ignore=True to overwrite")
except errors.InsufficientPermission:
    print("You don't have permission to upload files")
```

### Retry callback for logging

```python
def log_retries(sleeper, retries, args):
    print(f"Retry {retries}/{sleeper.max_retries} — args: {args}")

site = mwclient.Site('en.wikipedia.org', wait_callback=log_retries)
```

### Handle blocked users

```python
site = mwclient.Site('en.wikipedia.org')
site.login('MyBot', 'password')

if site.blocked:
    print(f"Bot is blocked: {site.blocked}")
else:
    page = site.pages['Some Page']
    page.save('content', summary='edit')
```

### Handle API errors by code

```python
try:
    page.save('content', summary='edit')
except errors.APIError as e:
    if e.code == 'editconflict':
        # Re-read and retry
        page = site.pages[page.name]  # Fresh page object
        old = page.text()
        page.save(old + '\nAppended text', summary='Retry after conflict')
    elif e.code == 'badtoken':
        # Token was stale — force refresh
        site.get_token('csrf', force=True)
        page.save('content', summary='Retry after token refresh')
    else:
        raise
```

---

## Advanced Patterns

### Batch editing with rate limiting

```python
import time

site = mwclient.Site('en.wikipedia.org')
site.login('MyBot', 'password')

pages_to_edit = ['Page1', 'Page2', 'Page3']
for title in pages_to_edit:
    page = site.pages[title]
    if page.exists:
        text = page.text()
        new_text = text.replace('old', 'new')
        page.save(new_text, summary='Batch replacement')
        time.sleep(5)  # Be polite to the server
```

### Copy page to another wiki

```python
site_src = mwclient.Site('source.wiki.org')
site_dst = mwclient.Site('dest.wiki.org', do_init=False)
site_dst.login('bot', 'password')

page_src = site_src.pages['Article']
text = page_src.text()

page_dst = site_dst.pages['Article']
page_dst.save(text, summary=f'Copied from source.wiki.org')
```

### Export pages to JSON

```python
import json

site = mwclient.Site('en.wikipedia.org')
pages = ['Python', 'Java', 'C++']

data = {}
for title in pages:
    page = site.pages[title]
    if page.exists:
        data[title] = {
            'text': page.text(),
            'pageid': page.pageid,
            'revision': page.revision,
        }

with open('pages_export.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### Semantic MediaWiki query

```python
site = mwclient.Site('wiki.example.org')
for result in site.ask('[[Category:Cities]] [[Population::>1000000]]'):
    print(result.get('printouts', {}))
```

### Raw API call

```python
# Direct API access for features mwclient doesn't wrap
result = site.api('query', prop='coordinates', titles='Oslo')
coords = result['query']['pages']
print(coords)
```

### Edit with all options

```python
page.save(
    text='New content',
    summary='Comprehensive edit',
    minor=False,
    bot=True,
    section=None,
    # Extra kwargs are passed to the API:
    recreate=True,      # Recreate if deleted
    createonly=False,    # Don't fail if exists
    nocreate=False,      # Don't fail if doesn't exist
    watchlist='nochange',
)
```
