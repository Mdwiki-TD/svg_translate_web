---
name: wikitextparser-tree-navigation
description: >
  Understand and navigate the wikitextparser tree. Covers parent() and
  ancestors() with the type_ filter, the supported type strings, the
  in-place mutation model (every child shares the root's buffer), how to
  delete nodes (del node[:] / del node.string), span containment via __contains__,
  and why there is no ast.walk-equivalent.
applies_to:
  - "parent()"
  - "ancestors()"
  - "nesting_level"
  - "del node[:]"
  - "in-place mutation"
  - "type_ filter"
---

# 12 — Tree Navigation & Mutation

> Open this file when you need to walk *up* the tree, find which template
> contains a given wikilink, or understand why setting a property mutates
> the entire article.

## When to use this file

Use this file for:

- Determining the context of a node (which template / section contains it).
- Understanding how mutation propagates from children to root.
- Removing nodes.
- Working around the lack of an `ast.walk()` equivalent.

## Mental model

```text
parsed (WikiText)
├── shared string buffer (mutable)
├── shared spans table  (every Template/WikiLink/.../Section has a span here)
└── every property like .templates returns wrappers pointing into that buffer

So:
    parsed.templates[0].set_arg('x', 'y')
       └─ mutates the shared buffer
       └─ str(parsed) reflects it instantly
       └─ no re-parse, no copy
```

The ergonomic upshot: **never rebuild the article string by hand.** Always
use the property setters, then read `str(parsed)`.

## Quick reference

| Operation                              | Purpose                                         |
| -------------------------------------- | ----------------------------------------------- |
| `node.parent()`                        | Nearest containing parsed node (any type)       |
| `node.parent(type_='Template')`        | Nearest template ancestor                       |
| `node.ancestors()`                     | All containing parsed nodes (closest first)     |
| `node.ancestors(type_='Section')`      | All ancestors of a specific type                |
| `node.nesting_level`                   | Depth count (specific to Template/PF/Table)     |
| `child in parent`                      | Span containment check (same root required)    |
| `del node[:]`                          | Remove this node from the buffer                |
| `del node.string`                      | Same as `del node[:]`                            |
| `node[a:b] = '...'`                    | In-place string surgery on this node            |

### Allowed `type_` values

The `type_` argument of `parent()` / `ancestors()` accepts these strings:

```text
'Template'
'ParserFunction'
'WikiLink'
'Comment'
'Parameter'
'ExtensionTag'   ← all extension tags (<ref>, <gallery>, ...)
```

These are the parser-detected span types. **Note:** `Section`, `Table`,
`WikiList`, `Bold`, `Italic`, `ExternalLink`, and ordinary HTML `Tag`
are **not** valid `type_` values for `ancestors()` — they are computed
on demand, not in the spans table.

## Step by step

### 1. Walk up to find a containing template

```python
parsed = wtp.parse("{{outer|x={{inner|y=[[Earth]]}}}}")
wl = parsed.wikilinks[0]                # [[Earth]]

wl.parent()                             # {{inner|...}}
wl.parent(type_='Template')             # {{inner|...}} (same here)
wl.ancestors()                          # [{{inner|...}}, {{outer|...}}]
wl.ancestors(type_='Template')[-1].name # 'outer'
```

### 2. Find which `<ref>` contains a wikilink

```python
for wl in parsed.wikilinks:
    ref = wl.parent(type_='ExtensionTag')
    if ref:
        print(wl.title, 'is inside an extension tag')
```

### 3. Detect top-level vs nested templates

```python
top_level = [t for t in parsed.templates if t.nesting_level == 0]
nested    = [t for t in parsed.templates if t.nesting_level > 0]
```

`nesting_level` is defined on `Template` and `ParserFunction`
(through `SubWikiTextWithArgs`) and on `Table`. It counts only the relevant
parent type.

### 4. Span containment check

```python
parsed = wtp.parse("{{a|{{b}}|x}}")
b = parsed.templates[1]
a = parsed.templates[0]
b in a    # True
a in b    # False
```

`__contains__` works only when both objects share the same `_lststr` (root
buffer). Two independent `wtp.parse(s)` calls produce separate buffers and
will report `False` even for identical content.

### 5. Delete a node

```python
for t in parsed.templates:
    if t.normal_name() == 'Cleanup':
        del t[:]
```

`del t[:]` removes the node's bytes from the buffer entirely, including the
surrounding `{{` and `}}`. After deletion, the node becomes a "dead" object
— attempts to mutate it raise `DeadIndexError`.

### 6. Replace a node

```python
for t in parsed.templates:
    if t.normal_name() == 'OldTemplate':
        t[:] = '{{NewTemplate|x=1}}'
```

Setting `node[:] = '...'` replaces the entire span. After the replacement
the original `Template` object's view points at the new content (it is
re-matched on next access).

### 7. Find every node of any type contained in a section

There is no `walk()` helper, but you can intersect lists:

```python
def nodes_in_section(parsed, section_index):
    s = parsed.sections[section_index]
    return {
        'templates'        : [t  for t  in parsed.templates if t in s],
        'wikilinks'        : [wl for wl in parsed.wikilinks if wl in s],
        'external_links'   : [el for el in parsed.external_links if el in s],
        'tables'           : [tb for tb in parsed.tables if tb in s],
        'comments'         : [c  for c  in parsed.comments  if c  in s],
    }
```

`x in s` works because `Section` shares the root buffer with all other nodes.

### 8. Distinguish "real ancestor" from "in same buffer"

```python
parsed = wtp.parse("{{a}}\n{{b}}")
a, b = parsed.templates
b.parent()          # None  — not nested under anything
b in parsed         # True  — both share the buffer
b in a              # False — span doesn't lie within a
```

## Edge cases & gotchas

- **`Section`, `Table`, `WikiList`, `Bold`, `Italic`, `ExternalLink`,
  `Tag` (HTML)** are *not* valid `type_` values for `parent()` /
  `ancestors()`. Use `'ExtensionTag'` for the subset of `Tag` that comes
  from `<ref>`, `<gallery>`, etc.
- **Iterate in reverse when deleting** to avoid invalidating earlier spans
  in the same loop:

  ```python
  for t in reversed(parsed.templates):
      if condition(t):
          del t[:]
  ```
- **A "dead" node** is one whose span has been deleted. Reading from it
  may return empty or stale content; mutating it raises `DeadIndexError`.
  Re-fetch via the property accessors after any structural delete.
- **Editing `parsed.string = ...`** replaces the entire buffer and
  invalidates *every* outstanding child object. Do this only at the
  beginning or end of a workflow.
- **`nesting_level` on Template** counts *only* template and parser-function
  ancestors. On `Table`, it counts table ancestors. There is no global
  "depth" property.
- **`ancestors()` is sorted by closeness** — the immediate parent is at
  index 0; the root is at index `-1`.
- **Two parsers, two buffers.** Comparing nodes from different `wtp.parse`
  calls is meaningless; `in` returns `False` even for textually identical
  content. Always operate on a single `parsed` object.

## Recipes

### Recipe A: which template contains each wikilink?

```python
def link_to_container_template(parsed) -> dict[str, str | None]:
    out = {}
    for wl in parsed.wikilinks:
        t = wl.parent(type_='Template')
        out[wl.title.strip()] = t.normal_name() if t else None
    return out
```

### Recipe B: tag every node in section "References"

```python
def is_in_references(node, parsed) -> bool:
    for s in parsed.sections:
        if s.title and s.title.strip() == 'References' and node in s:
            return True
    return False
```

### Recipe C: cascade-delete a template and everything that referenced it

```python
target = 'Outdated'
for t in parsed.templates:
    if t.normal_name() == target:
        for nested in t.templates:
            del nested[:]
        del t[:]
```

### Recipe D: collect templates by section

```python
def templates_per_section(parsed) -> dict[str, list[str]]:
    out = {}
    for s in parsed.sections:
        title = (s.title or '<lead>').strip()
        out[title] = [
            t.normal_name() for t in parsed.templates if t in s
        ]
    return out
```

### Recipe E: count refs nested inside templates vs free-standing

```python
nested_in_template = 0
free = 0
for ref in parsed.get_tags('ref'):
    if ref.parent(type_='Template') is not None:
        nested_in_template += 1
    else:
        free += 1
```

## See also

- `01-wikitext-basics.md` — the in-place mutation model
- `02-templates.md` — `nesting_level`, ordering of arguments
- `references/reference.md` — full SubWikiText API
