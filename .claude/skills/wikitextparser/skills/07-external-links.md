---
name: wikitextparser-external-links
description: >
  Read and modify external links — both bracketed [https://example.com text]
  and bare URLs (http://example.com). Covers ExternalLink.url, .text,
  .in_brackets, the auto-bracketing behaviour of setters, and the edge case
  of templates immediately following a URL being captured into the URL.
applies_to:
  - "ExternalLink"
  - "[https://...]"
  - "[https://... text]"
  - "http://..."
  - "external_links"
---

# 07 — External Links (`[url text]` and bare URLs)

> Open this file when you need to extract or rewrite outbound URLs. These
> are different from `[[wikilinks]]` (single brackets vs double brackets).

## When to use this file

Use this file for:

- Listing every URL in a page.
- Filtering by domain.
- Adding or removing display text.
- Converting bare URLs to bracketed links and vice versa.

## Mental model

Two flavours:

```
Bare:        https://example.com/page
Bracketed:   [https://example.com/page Display text]
Bracketed:   [https://example.com/page]              ← no text
```

`ExternalLink` exposes:

| Property      | Bare URL                 | `[url text]`        | `[url]`             |
| ------------- | ------------------------ | ------------------- | ------------------- |
| `el.url`      | the URL                  | the URL             | the URL             |
| `el.text`     | `None`                   | `'text'`            | `None`              |
| `el.in_brackets` | `False`               | `True`              | `True`              |

## Quick reference

| Property / setter / deleter   | Behaviour                                                     |
| ----------------------------- | ------------------------------------------------------------- |
| `el.url`                      | Get or set URL. Setter on bare links replaces in place        |
| `el.text`                     | Get or set text. Setter auto-adds brackets if currently bare  |
| `del el.text`                 | Removes text + space. No-op on bare links                     |
| `el.in_brackets`              | Read-only `bool`                                              |

## Step by step

### 1. List all external links

```python
parsed = wtp.parse("See https://example.com or [https://example.org docs]")
for el in parsed.external_links:
    print(el.url, '|', el.text, '|', el.in_brackets)
# https://example.com  | None | False
# https://example.org  | docs | True
```

### 2. Filter by domain

```python
def links_to(parsed, domain: str) -> list:
    domain = domain.lower()
    return [el for el in parsed.external_links
            if domain in el.url.lower()]
```

### 3. Change a URL

```python
el = parsed.external_links[0]
el.url = 'https://archive.org/page'
```

The setter preserves brackets if the link was bracketed, and stays bare
otherwise.

### 4. Add display text to a bare link

```python
parsed = wtp.parse('https://example.com')
el = parsed.external_links[0]
el.text = 'Example'
str(parsed)        # '[https://example.com Example]'
```

The setter wraps the URL in brackets automatically when needed.

### 5. Remove display text

```python
parsed = wtp.parse('[https://example.com Example]')
el = parsed.external_links[0]
del el.text
str(parsed)        # '[https://example.com]'
```

`del el.text` is a no-op on bare links.

### 6. Convert bracketed → bare manually

There is no built-in "unbracket" operation. Replace the whole link:

```python
for el in parsed.external_links:
    if el.in_brackets and el.text is None:
        # [https://example.com] → https://example.com
        el[:] = el.url
```

## Edge cases & gotchas

- **Templates adjacent to a bare URL get sucked into the URL.** This is a
  well-known parser quirk that mirrors MediaWiki's own behaviour:

  ```python
  el = wtp.parse('http://example.com{{dead link}}').external_links[0]
  el.url     # 'http://example.com{{dead link}}'   ← yes, the template too
  ```

  If you need to strip such tails, post-process `el.url` with a regex.
- **Bracketed links without a space** like `[https://example.com]` have
  `el.text == None`. Don't confuse with empty text.
- **Schemes**: bare URLs are matched only for whitelisted schemes (`http`,
  `https`, `ftp`, `news`, `gopher`, `mailto`, `irc`, `telnet`, etc.).
  Inside brackets, additional schemes including protocol-relative `//` are
  accepted.
- **A bare URL inside a `[[wikilink]]`** is *not* captured as an external
  link — it is part of the wikilink target/text.
- **`el.external_links`** on an ExternalLink object returns `[]` — they
  cannot nest.
- **Trailing punctuation** in bare URLs (e.g. `https://example.com.`) is
  excluded from the URL by the regex; the dot stays in the surrounding text.

## Recipes

### Recipe A: list every external URL with its anchor text

```python
def url_inventory(wikitext: str) -> list[dict]:
    parsed = wtp.parse(wikitext)
    return [
        {'url': el.url, 'text': el.text, 'in_brackets': el.in_brackets}
        for el in parsed.external_links
    ]
```

### Recipe B: count distinct domains

```python
from urllib.parse import urlparse
from collections import Counter

domains = Counter()
for el in parsed.external_links:
    try:
        domains[urlparse(el.url).netloc.lower()] += 1
    except ValueError:
        pass
```

### Recipe C: archive.org rewrite

```python
def to_archive(parsed, snapshot='*'):
    for el in parsed.external_links:
        if el.url.startswith(('http://', 'https://')):
            el.url = f'https://web.archive.org/web/{snapshot}/{el.url}'
```

### Recipe D: ensure every bare URL has anchor text

```python
for el in parsed.external_links:
    if not el.in_brackets:
        el.text = el.url   # promotes bare → bracketed with self-text
```

### Recipe E: strip tracking parameters

```python
import re
for el in parsed.external_links:
    el.url = re.sub(r'([?&])(utm_[^=&]+|fbclid|gclid)=[^&]*', r'\1', el.url)
    el.url = re.sub(r'[?&]+$', '', el.url)
```

## See also

- `04-wikilinks.md` — internal `[[wikilinks]]` (different syntax)
- `01-wikitext-basics.md` — `plain_text(replace_external_links=...)`
- `references/reference.md` — full ExternalLink API
