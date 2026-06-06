---
name: wikitextparser-sections
description: >
  Navigate and modify article sections (== Heading ==, === Sub ===). Covers
  the Section class, the special "lead" section at index 0, level/title/contents
  setters, level promotion and demotion, and filtered access via
  get_sections(level=, include_subsections=, top_levels_only=).
applies_to:
  - "Section"
  - "== Heading =="
  - "lead section"
  - "get_sections"
  - "level"
---

# 08 — Sections

> Open this file when you need to walk article structure, rename headings,
> change heading levels, or extract a particular section's body.

## When to use this file

Use this file for:

- Splitting an article by `==` headings.
- Renaming section titles.
- Promoting `===` to `==` (or the reverse).
- Extracting just the body of a named section.

## Mental model

A section is the heading **plus** everything until the next heading of the
same or shallower level. The very first "section" is the **lead** — the
content above the first heading. The lead has `level == 0` and `title is
None`.

```text
Lead text                       ← Section(level=0, title=None)
== Section A ==                 ← Section(level=2, title='Section A')
content
=== Section A.1 ===             ← Section(level=3, title='Section A.1')
sub content
== Section B ==                 ← Section(level=2, title='Section B')
```

By default, `parsed.sections` returns nested sections **with** their
sub-sections folded into `contents`, so you can iterate top-to-bottom and
get whole subtrees at the high-level entries. Use `include_subsections=False`
to see only the raw text of each individual heading scope.

## Quick reference

| Operation                                                          | Returns                |
| ------------------------------------------------------------------ | ---------------------- |
| `parsed.sections`                                                  | All sections (lead first) |
| `parsed.get_sections(level=N)`                                     | Only sections at level N  |
| `parsed.get_sections(include_subsections=False)`                   | Sections without nested children |
| `parsed.get_sections(top_levels_only=True)`                        | Top-level sections only (level cannot be passed) |
| `s.title`                                                          | Heading text (no `=`). Lead → `None`. Set/del. |
| `s.level`                                                          | 1–6 for headings; 0 for lead. Set to promote/demote. |
| `s.contents`                                                       | Body text after the heading line. Set to replace. |

## Step by step

### 1. Walk every section

```python
for s in parsed.sections:
    print(s.level, '|', s.title, '|', len(s.contents))
```

`parsed.sections` always includes the lead at index 0, even when empty.

### 2. Read the body of a named section

```python
def section_body(parsed, title: str) -> str | None:
    for s in parsed.sections:
        if s.title and s.title.strip() == title:
            return s.contents
    return None
```

### 3. Rename a section heading

```python
for s in parsed.sections:
    if s.title and s.title.strip() == 'See also':
        s.title = 'References'
```

### 4. Promote / demote levels

Setting `s.level = N` adjusts the number of `=` signs:

```python
for s in parsed.sections:
    if s.level >= 3:
        s.level = s.level - 1     # === → ==
```

The setter inserts or removes the appropriate number of `=` on both sides.
Levels are clamped between 1 and 6 by MediaWiki itself; the library lets
you set any positive integer — but going outside the 1–6 range produces
output that MediaWiki will not recognise as a heading.

### 5. Filter by level

```python
parsed.get_sections(level=2)                        # only `== ==`
parsed.get_sections(include_subsections=False)      # no nested folding
parsed.get_sections(top_levels_only=True)           # only sections that are not subsections of another
```

`top_levels_only=True` cannot be combined with `level=...` — pick one.

### 6. Replace section body

```python
for s in parsed.sections:
    if s.title and s.title.strip() == 'Notes':
        s.contents = '\n<references/>\n'
```

`s.contents` setter replaces everything between the heading line and the
end of the section's span.

### 7. Insert a new section

There is no "create section" helper. Append to the article string:

```python
parsed.string = str(parsed).rstrip() + '\n\n== New section ==\nContent\n'
```

Then re-fetch `parsed.sections` if you want to manipulate the new one.

### 8. Delete a section heading (keep the body)

```python
for s in parsed.sections:
    if s.title and s.title.strip() == 'Trivia':
        del s.title
```

`del s.title` removes the heading line plus the trailing newline; the body
remains as plain text in the previous section.

### 9. Delete a whole section (heading + body)

```python
for s in parsed.sections:
    if s.title and s.title.strip() == 'Trivia':
        del s[:]
```

`del s[:]` removes the entire span from the buffer.

## Edge cases & gotchas

- **You cannot set the title of the lead section.** Doing so raises
  `RuntimeError("Can't set title for a lead section. Try adding it to
  contents.")` because the lead has no `=` signs to replace. Modify
  `s.contents` instead.
- **Heading lines must end with the matching number of `=` signs.** Stray
  text after the closing `=` (like trailing spaces) is allowed — the
  library matches `(={1,6})...\1[ \t]*(\n|\Z)`.
- **`include_subsections=True` (default) gives overlapping sections.**
  A `== A ==` section that contains `=== A.1 ===` will appear once with
  `A.1` folded into its `contents`, and `A.1` also appears as its own
  separate entry. Both are valid views of the same buffer.
- **Section levels do not auto-correct.** If you demote `== A ==` to
  `=== A ===` while its previous parent was also `== ==`, you create an
  invalid hierarchy in the output. The library does not validate this;
  it's your job.
- **Tables-of-contents magic words** (`__TOC__`, `__NOTOC__`) are not
  parsed specially — they are part of the surrounding text.
- **Section objects share the underlying buffer.** Mutating one section's
  `contents` invalidates spans of later sections — re-fetch
  `parsed.sections` after any structural edit.

## Recipes

### Recipe A: list TOC entries

```python
def toc(parsed) -> list[tuple[int, str]]:
    return [(s.level, s.title.strip()) for s in parsed.sections
            if s.title is not None]
```

### Recipe B: rename a section

```python
def rename_section(wikitext, old, new) -> str:
    parsed = wtp.parse(wikitext)
    for s in parsed.sections:
        if s.title and s.title.strip() == old:
            s.title = new
    return str(parsed)
```

### Recipe C: promote all sections one level (h3 → h2 etc.)

```python
def promote_all(parsed):
    for s in parsed.sections:
        if s.level >= 2:
            s.level = s.level - 1
```

Iterate via `get_sections(include_subsections=False)` if you want each
heading processed exactly once.

### Recipe D: extract every section as `(title, body)` records

```python
def split_sections(parsed) -> list[dict]:
    out = []
    for s in parsed.get_sections(include_subsections=False):
        out.append({
            'level': s.level,
            'title': s.title.strip() if s.title else '',
            'body' : s.contents.strip(),
        })
    return out
```

### Recipe E: append a new sub-section under "References"

```python
def add_subsection(wikitext, parent_title, new_subtitle, new_body):
    parsed = wtp.parse(wikitext)
    for s in parsed.sections:
        if s.title and s.title.strip() == parent_title:
            new = f"\n=== {new_subtitle} ===\n{new_body}\n"
            s.contents = (s.contents.rstrip() + new + '\n')
            return str(parsed)
    return wikitext
```

## See also

- `01-wikitext-basics.md` — `parsed.string`, in-place mutation rules
- `12-tree-navigation.md` — finding which section contains a node
- `references/reference.md` — full Section API
