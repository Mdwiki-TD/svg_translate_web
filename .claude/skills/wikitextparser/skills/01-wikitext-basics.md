---
name: wikitextparser-basics
description: >
  Fundamentals of the wikitextparser root API: parsing, the WikiText object,
  string round-tripping, plain-text extraction, pretty-printing, and the
  relationship between nodes and their underlying buffer. Read this first,
  before any of the type-specific sub-skills.
applies_to:
  - "wtp.parse(...)"
  - "WikiText"
  - "plain_text()"
  - "remove_markup()"
  - "pformat()"
  - "str(parsed)"
  - "parsed[i:j]"
---

# 01 — WikiText Basics

> Open this file when you need to know **how `wtp.parse` works**, how the
> resulting object behaves like a string, or how to convert wikitext to clean
> text or pretty-printed form.

## When to use this file

Use this file for:

- Understanding what `wtp.parse(s)` returns.
- Converting wikitext to plain text (`plain_text()`, `remove_markup`).
- Pretty-printing templates (`pformat`).
- The string-like access patterns: `str(parsed)`, `parsed.string`,
  `parsed[i:j]`, `len(parsed)`.

For type-specific extraction (templates, links, tables, ...) jump directly to
the relevant sub-skill listed in `SKILL.md`.

## Mental model

`wtp.parse(s)` returns a `WikiText` object that wraps a **single mutable
string list** shared by every descendant node. Every property like
`.templates`, `.wikilinks`, etc. returns objects that still point into that
shared buffer — modifying any child mutates the root in place. There is no
re-parse step and no copy.

```text
                  ┌────────────────────────┐
parsed (WikiText) │ "Hello {{t|x=1}} world"│   ← shared buffer
  ├─ Template ────┤        ^^^^^^^^         │
  └─ Argument ────┤            ^^^          │
                  └────────────────────────┘
```

## Quick reference

| Operation                          | Returns           | Notes                                    |
| ---------------------------------- | ----------------- | ---------------------------------------- |
| `wtp.parse(s)`                     | `WikiText`        | Alias of `wtp.WikiText(s)`               |
| `str(parsed)`                      | `str`             | Current buffer state (after edits)       |
| `parsed.string`                    | `str`             | Same as `str(parsed)`. Get/set/delete    |
| `parsed[i:j]`                      | `str`             | Slice. Setter does in-place surgery      |
| `parsed(start, stop=False)`        | `str`             | Faster slice; `parsed(0)` → first char   |
| `len(parsed)`                      | `int`             | Length of the node's span                |
| `parsed.span`                      | `tuple[int, int]` | Start and end offset within root         |
| `value in parsed`                  | `bool`            | True if a node lies inside this node     |
| `parsed.plain_text(...)`           | `str`             | Stripped/replaced text                   |
| `wtp.remove_markup(s, ...)`        | `str`             | Same as above, standalone function       |
| `parsed.pformat(indent='    ')`    | `str`             | Pretty-printed copy (does **not** mutate)|

## Step by step

### 1. Parse a string

```python
import wikitextparser as wtp

parsed = wtp.parse("Hello '''world''' and [[Earth]]")
print(type(parsed).__name__)   # WikiText
print(str(parsed))             # 'Hello \'\'\'world\'\'\' and [[Earth]]'
```

### 2. Round-trip (parse → mutate → emit)

```python
parsed = wtp.parse("{{Person|name=Alice|age=30}}")
parsed.templates[0].set_arg('age', '31')
print(str(parsed))   # '{{Person|name=Alice|age=31}}'
```

The original input string is never re-parsed. The buffer has been mutated.

### 3. Plain text extraction

`plain_text()` strips or replaces every wikitext construct. Each construct is
controlled by a keyword argument; defaults remove or replace everything.

```python
parsed = wtp.parse("'''Bold''' [[Earth|home]] {{ref|x}} <!-- hidden -->")

parsed.plain_text()
# → "Bold home  "
```

Most useful flags:

| Flag                          | Default | Effect                                                |
| ----------------------------- | ------- | ----------------------------------------------------- |
| `replace_templates`           | `True`  | `True` → drop; `False` → keep; callable → custom text |
| `replace_parser_functions`    | `True`  | Same as above                                         |
| `replace_parameters`          | `True`  | `{{{a\|b}}}` → `b`, `{{{a}}}` → `''`                  |
| `replace_tags`                | `True`  | `<s>x</s>` → `x`                                      |
| `replace_external_links`      | `True`  | `[url text]` → `text`, bare URL → ''                  |
| `replace_wikilinks`           | `True`  | `[[a\|b]]` → `b`, `[[a]]` → `a`. Files always removed.|
| `unescape_html_entities`      | `True`  | `&amp;` → `&`                                         |
| `replace_bolds_and_italics`   | `True`  | strips `'''`, `''`                                    |
| `replace_tables`              | callable| default converter renders tables as TSV-style text    |

Comments (`<!-- ... -->`) are **always** removed.

#### Custom replacement via callable

```python
# Keep templates but replace each with its name
parsed.plain_text(replace_templates=lambda t: '{{%s}}' % t.normal_name())
```

#### Standalone function form

```python
from wikitextparser import remove_markup
remove_markup("Hello '''world''' [[Earth]]")
# → 'Hello world Earth'
```

`remove_markup(s, **kwargs)` is exactly equivalent to
`wtp.parse(s).plain_text(**kwargs, _is_root_node=True)`.

### 4. Pretty-print templates

```python
parsed = wtp.parse("{{Infobox|name=Alice|age=30|nationality=US}}")
print(parsed.pformat())
```

```
{{Infobox
 | name        = Alice
 | age         = 30
 | nationality = US
}}
```

Notes:

- `pformat()` returns a **new string**; the original buffer is unchanged.
- `pformat(remove_comments=True)` strips all comments before formatting.
- Pretty-printing aligns `=` signs across all keyword arguments.
- Positional arguments and parser-function-like templates (containing `:`) are
  treated more conservatively — they may not be re-aligned to avoid breaking
  whitespace-sensitive output.

### 5. String-like operations

```python
parsed = wtp.parse("== Lead ==\nbody")
parsed[0:7]                 # '== Lead'
parsed(0, 7)                # '== Lead'  (faster — avoids creating .string)
parsed(0)                   # '='
len(parsed)                 # 14
'body' in parsed            # True (substring check)
some_template in parsed     # True if same root and inside this span
```

The `__call__` form is preferred internally because it avoids materialising
the full `.string` property. Use it when you slice a lot.

### 6. Containment vs identity

```python
parsed1 = wtp.parse("{{a}}")
parsed2 = wtp.parse("{{a}}")
parsed1.templates[0] in parsed2   # False — different roots
parsed1.templates[0] in parsed1   # True
```

`in` checks both *span containment* and *same root list*. Two parses of the
same string are independent.

## Edge cases & gotchas

- **`pformat()` does not mutate.** Reassign if you want to keep the result:
  `wikitext = parsed.pformat()`.
- **`plain_text()` returns a string, not a `WikiText`.** Re-parse if you need
  to walk the cleaned content.
- **Files are always stripped from `plain_text()`** even with
  `replace_wikilinks=False`, because they are visually rendered as images
  rather than text.
- **`remove_markup` and `parsed.plain_text()` are not perfectly identical** in
  intermediate behaviour: `remove_markup` builds a new root; `plain_text()`
  works on a copy of the spans. The output is the same; performance differs
  slightly on deeply-nested input.
- **Comments cannot be preserved** by `plain_text` — they are removed
  unconditionally.
- **Setting `parsed.string = '...'`** replaces the entire buffer and
  invalidates every previously-extracted child object. Treat such children as
  dead and re-fetch via the property accessors.

## Recipes

### Recipe 1: NLP-friendly cleanup

```python
def to_clean_text(wikitext: str) -> str:
    return wtp.parse(wikitext).plain_text(
        replace_templates=True,
        replace_parser_functions=True,
        replace_parameters=True,
        replace_tags=True,
        replace_external_links=True,
        replace_wikilinks=True,
        unescape_html_entities=True,
        replace_bolds_and_italics=True,
    ).strip()
```

### Recipe 2: Keep wikilink display text but strip everything else

```python
def link_aware_text(wikitext: str) -> str:
    parsed = wtp.parse(wikitext)
    return parsed.plain_text(
        replace_wikilinks=True,   # [[a|b]] → 'b'
        replace_templates=True,
        replace_external_links=True,
    )
```

### Recipe 3: Pretty-print every template in an article

```python
def pp_all_templates(wikitext: str) -> str:
    parsed = wtp.parse(wikitext)
    return '\n\n'.join(t.pformat() for t in parsed.templates)
```

## See also

- `02-templates.md` — full template/argument API
- `12-tree-navigation.md` — how mutation and parents/ancestors work
- `13-common-patterns.md` — combined recipes
- `references/reference.md` — full method signatures
