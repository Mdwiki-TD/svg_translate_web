---
name: wikitextparser-tags-comments
description: >
    Work with HTML/MediaWiki extension tags (<ref>, <gallery>, <nowiki>, <math>,
    <syntaxhighlight>, <references/>), comments (<!-- -->), and bold/italic
    spans ('''bold''' / ''italic''). Covers Tag attributes API
    (get_attr/set_attr/has_attr/del_attr), parsed_contents, self-closing-tag
    expansion, named/reused refs, get_bolds/get_italics/get_bolds_and_italics.
applies_to:
    - "Tag"
    - "Comment"
    - "Bold"
    - "Italic"
    - "<ref>"
    - "<ref name=...>"
    - "<gallery>"
    - "<nowiki>"
    - "<syntaxhighlight>"
    - "<math>"
    - "<!-- -->"
    - "'''bold'''"
    - "''italic''"
---

# 10 — Tags, Comments, Bold & Italic

> Open this file when you need to work with HTML or MediaWiki extension tags
> (`<ref>`, `<gallery>`, ...), HTML comments, or bold/italic spans.

## When to use this file

Use this file for:

-   Extracting `<ref>` citations.
-   Reading or modifying tag HTML attributes.
-   Walking comments.
-   Listing every `'''bold'''` or `''italic''` span.

For `<gallery>` content parsing specifically, see `05-categories-files.md`.

## Mental model

`Tag` covers two things uniformly:

1. **HTML-like tags** that MediaWiki passes through: `<span>`, `<div>`,
   `<sup>`, `<small>`, ...
2. **Extension tags** that MediaWiki implements specially: `<ref>`,
   `<references/>`, `<gallery>`, `<nowiki>`, `<math>`, `<syntaxhighlight>`,
   `<pre>`, `<source>`, `<timeline>`, etc.

Both share the same API. Self-closing tags (`<ref/>`) have `contents == None`
until you assign to `contents`, at which point they expand to a normal
open/close pair.

`Comment` represents `<!-- ... -->`. Its contents are read-only.

`Bold` and `Italic` represent `'''text'''` and `''text''`. They expose
`.text` as a read-write property (get returns the inner text; set replaces it
in place while preserving the surrounding quote tokens).

## Quick reference

### Tag

| Attribute / method          | Description                                      |
| --------------------------- | ------------------------------------------------ |
| `parsed.get_tags()`         | All tags                                         |
| `parsed.get_tags('ref')`    | All `<ref>` tags                                 |
| `tag.name`                  | Tag name (string). Get/set                       |
| `tag.contents`              | Inner content (`None` for self-closing). Get/set |
| `tag.parsed_contents`       | `SubWikiText` view of the contents               |
| `tag.attrs`                 | Dict of all HTML attributes                      |
| `tag.get_attr(name)`        | Last value, or `None`                            |
| `tag.set_attr(name, value)` | Update last, or insert if missing                |
| `tag.has_attr(name)`        | `bool`                                           |
| `tag.del_attr(name)`        | Remove all with that name                        |
| `tag.get_tags(name=None)`   | Tags nested inside this tag (excludes self)      |

### Comment

| Attribute         | Description                               |
| ----------------- | ----------------------------------------- |
| `parsed.comments` | All `<!-- ... -->` comments               |
| `c.contents`      | Text between `<!--` and `-->` (read-only) |

### Bold / Italic

| Attribute / method                                              | Description                                                    |
| --------------------------------------------------------------- | -------------------------------------------------------------- |
| `parsed.get_bolds(recursive=True)`                              | All `Bold` spans                                               |
| `parsed.get_italics(recursive=True)`                            | All `Italic` spans                                             |
| `parsed.get_bolds_and_italics(recursive=True, filter_cls=None)` | Combined (more efficient than two calls)                       |
| `b.text` / `i.text`                                             | Inner text without the quote tokens. Get/set                   |
| `Italic(..., end_token=False)`                                  | Internal: represents an unclosed italic span (no closing `''`) |

## Step by step

### 1. List `<ref>` tags

```python
parsed = wtp.parse('Cite.<ref name="x">Smith 2020</ref> More.<ref name="x"/>')
for ref in parsed.get_tags('ref'):
    print(ref.get_attr('name'), '|', ref.contents)
# x | Smith 2020
# x | None         ← self-closing reuse
```

### 2. Filter named-only refs vs reused refs

```python
named = []
inline = []
reused = []
for r in parsed.get_tags('ref'):
    name = r.get_attr('name')
    body = r.contents
    if body is None:
        reused.append(r)         # <ref name="x"/>  — pointer to a previous ref
    elif name:
        named.append(r)          # <ref name="x">...</ref>
    else:
        inline.append(r)         # <ref>...</ref>
```

### 3. Read tag attributes

```python
for tag in parsed.get_tags('cite'):
    tag.attrs                    # {'class': 'book', 'data-x': '1'}
    tag.get_attr('class')        # 'book'
    tag.has_attr('id')           # False
```

### 4. Modify tag attributes

```python
for ref in parsed.get_tags('ref'):
    if not ref.has_attr('group'):
        ref.set_attr('group', 'sources')
    ref.del_attr('xml:lang')
```

### 5. Modify tag contents

```python
for ref in parsed.get_tags('ref'):
    if ref.contents is not None:
        # Wrap citations in a {{cite ... }} template
        ref.contents = ref.contents.strip()
```

#### Self-closing → paired

```python
tag = wtp.parse('<gallery/>').get_tags('gallery')[0]
tag.contents                # None
tag.contents = 'image1.jpg|caption'
str(tag)                    # '<gallery>image1.jpg|caption</gallery>'
```

Setting `contents` on a self-closing tag automatically expands it to a
proper open/close pair.

### 6. Rename a tag

```python
for tag in parsed.get_tags('s'):
    tag.name = 'del'
# <s>...</s>  →  <del>...</del>
```

The setter renames _both_ the start and end tag.

### 7. Walk parsed_contents

```python
ref = parsed.get_tags('ref')[0]
ref.parsed_contents                    # SubWikiText pointing into ref body
ref.parsed_contents.templates          # templates inside the ref
ref.parsed_contents.wikilinks          # wikilinks inside the ref
```

`parsed_contents` is the right way to apply the full WikiText API to a
tag's body without re-parsing.

### 8. Comments

```python
for c in parsed.comments:
    print(c.contents)
```

`Comment.contents` is read-only. To remove a comment:

```python
del c[:]
```

### 9. Bold and italic

```python
for b in parsed.get_bolds():
    print('bold:', b.text)

for i in parsed.get_italics():
    print('italic:', i.text)
```

#### Combined call (efficient)

```python
for span in parsed.get_bolds_and_italics():
    kind = type(span).__name__
    print(kind, ':', span.text)
```

#### Filter by class

```python
parsed.get_bolds_and_italics(filter_cls=wtp.Bold)
parsed.get_bolds_and_italics(filter_cls=wtp.Italic)
```

#### Modify bold/italic text

```python
for b in parsed.get_bolds():
    b.text = b.text.upper()
```

## Edge cases & gotchas

-   **Tags inside templates / wikilinks** are still found; pass
    `recursive=True` (default) on `get_bolds_and_italics`.
-   **`tag.contents`** is `None` only when the tag is genuinely self-closing
    in source (`<x/>` or `<x />`). An empty paired tag (`<x></x>`) has
    `contents == ''`.
-   **`tag.attrs` keys/values are decoded strings**, but the underlying
    matcher works on bytes — exotic UTF-8 attribute values may round-trip
    through `.encode('ascii', 'replace')`. For ASCII-only attributes (the
    norm) this is fine.
-   **`<ref name="x"/>` reuse** has `contents is None`. Don't compare against
    `''`.
-   **Bold/italic spans terminate at line-end.** A `'''text` without closing
    `'''` is still parsed as a bold span up to end-of-line — for italics,
    the library exposes `Italic(end_token=False)` to represent unclosed
    ones.
-   **`<nowiki>` content is opaque.** Its inner text is not re-parsed for
    templates/wikilinks. To get raw nowiki content, read `tag.contents`
    directly.
-   **Comments inside tags** are still parsed and listed in
    `parsed.comments` — not as nested under the enclosing tag in any tree
    sense, but found via the global list.
-   **Bold-italic (`'''''text'''''`)** can be returned as either Bold or
    Italic depending on context. Use `get_bolds_and_italics()` if you want
    both kinds without missing any.
-   **Setting `tag.name = 'X'`** also renames the closing tag; if the closing
    tag was missing (malformed input), only the opening name is changed.

## Recipes

### Recipe A: extract every citation

```python
def extract_refs(parsed) -> list[dict]:
    out = []
    for r in parsed.get_tags('ref'):
        out.append({
            'name'   : r.get_attr('name'),
            'group'  : r.get_attr('group'),
            'content': (r.contents or '').strip() or None,
        })
    return out
```

### Recipe B: rename a `<ref>` group

```python
for r in parsed.get_tags('ref'):
    if r.get_attr('group') == 'note':
        r.set_attr('group', 'notes')
```

### Recipe C: replace `<s>` with `<del>` (deprecated tag cleanup)

```python
for tag in parsed.get_tags('s'):
    tag.name = 'del'
```

### Recipe D: drop all comments

```python
for c in parsed.comments:
    del c[:]
```

(Or, when producing plain text, just call `parsed.plain_text()` — it
removes comments unconditionally.)

### Recipe E: convert all italic to `<em>` HTML

```python
for it in parsed.get_italics():
    it[:] = f'<em>{it.text}</em>'
```

### Recipe F: list every block-quoted text inside a `<blockquote>`

```python
quotes = []
for tag in parsed.get_tags('blockquote'):
    if tag.contents:
        # Strip wiki markup inside
        clean = wtp.parse(tag.contents).plain_text()
        quotes.append(clean.strip())
```

## See also

-   `05-categories-files.md` — `<gallery>` parsing
-   `01-wikitext-basics.md` — `plain_text(replace_tags=...)`
-   `references/reference.md` — full Tag/Comment/Bold/Italic API
