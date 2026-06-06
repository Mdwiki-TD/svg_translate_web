---
name: wikitextparser-templates
description: >
  Read and modify MediaWiki templates ({{template|args}}) — the most common
  task in wikitext processing. Covers the Template class, name canonicalization,
  the Argument class, get_arg/set_arg/has_arg/del_arg, positional vs keyword
  arguments, duplicate-argument cleanup (rm_dup_args_safe vs
  rm_first_of_dup_args), template pretty-printing, and nested templates.
applies_to:
  - "Template"
  - "Argument"
  - "{{template|...}}"
  - "Infobox"
  - "set_arg"
  - "normal_name"
---

# 02 — Templates

> Open this file when you need to read, validate, or modify any
> `{{template|...}}` call. This is by far the most common wikitext task.

## When to use this file

Use this file for:

- Extracting an infobox or any template's parameters as a dict.
- Finding all uses of a specific template across an article.
- Setting, renaming, or deleting template arguments.
- Cleaning up duplicate arguments.
- Pretty-printing or normalising template names.

For `{{{name|default}}}` (template-parameter declarations on `/doc` subpages),
see **`03-parameters.md`** — those are a different syntactic construct.

## Mental model

A template `{{Foo|x=1|2|y=3}}` is a `Template` object wrapping `{{...}}` and
exposing two pieces of info:

1. **`name`** — everything between `{{` and the first `|` (or `}}` if no args).
2. **`arguments`** — every pipe-separated chunk after that, each becoming an
   `Argument` object.

Each `Argument` is either **positional** (no `=`) or **keyword** (has `=`).
Positional arguments expose their position as a string name (`"1"`, `"2"`,
`...`). Whitespace inside keyword values is stripped by MediaWiki at render
time but preserved in the source — `wikitextparser` mirrors this.

## Quick reference

### Template

| Attribute / method                                                              | Description                                  |
| ------------------------------------------------------------------------------- | -------------------------------------------- |
| `t.name`                                                                        | Raw name string (may include whitespace)     |
| `t.normal_name(rm_namespaces=('Template',), code=None, capitalize=False)`       | Canonicalized name                           |
| `t.arguments`                                                                   | `list[Argument]`                             |
| `t.get_arg(name)`                                                               | `Argument` or `None` (last match wins)       |
| `t.has_arg(name, value=None)`                                                   | `bool`                                       |
| `t.set_arg(name, value, positional=None, before=None, after=None, preserve_spacing=False)` | Insert/update; see below       |
| `t.del_arg(name)`                                                               | Delete all args with that name               |
| `t.rm_dup_args_safe(tag=None)`                                                  | Lossless dup cleanup                         |
| `t.rm_first_of_dup_args()`                                                      | Aggressive dup cleanup                       |
| `t.pformat(indent='    ', remove_comments=False)`                               | Pretty-printed string                        |
| `t.templates`                                                                   | Templates nested inside `t` (excludes self)  |
| `t.nesting_level`                                                               | 0 = top-level; +1 per enclosing template/PF  |

### Argument

| Attribute       | Description                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------------ |
| `arg.name`      | Keyword arg → its name; positional arg → its position as string (`"1"`)                                |
| `arg.value`     | Value (read/write)                                                                                     |
| `arg.positional`| `True` for positional. Setter can convert keyword → positional; setting `False` raises `ValueError` (use `arg.name = ...` instead) |

## Step by step

### 1. Get all templates from an article

```python
parsed = wtp.parse(article)
for t in parsed.templates:
    print(t.normal_name())
```

`parsed.templates` includes nested templates as separate top-level entries.
Outer templates appear first.

### 2. Find a specific template

```python
def find_templates(parsed, name: str):
    return [t for t in parsed.templates
            if t.normal_name().lower() == name.lower()]

infoboxes = find_templates(parsed, 'Infobox person')
```

Always compare via `normal_name()` — never `t.name` raw — because the name in
source can have leading/trailing whitespace, underscores, comments, or even
the `Template:` prefix:

```python
t = wtp.parse('{{ eN : tEmPlAtE : <!-- c --> t_1 # b | a }}').templates[0]
t.name           # ' eN : tEmPlAtE : <!-- c --> t_1 # b '
t.normal_name(code='en')   # 'T 1'
```

`normal_name(code=...)` is meant for interwiki names like `{{en:Template:Foo}}`.

### 3. Read arguments as a dict

```python
def template_to_dict(t) -> dict:
    return {arg.name.strip(): arg.value.strip()
            for arg in t.arguments
            if not arg.positional}

data = template_to_dict(parsed.templates[0])
print(data['name'], data['birth_date'])
```

For ordered positional args (e.g. `{{convert|10|km|mi}}`):

```python
positional = [arg.value for arg in t.arguments if arg.positional]
# positional == ['10', 'km', 'mi']
```

### 4. Get a single argument safely

```python
arg = t.get_arg('birth_date')
if arg is not None:
    print(arg.value.strip())
```

`get_arg` returns the **last** argument with that name (which is what
MediaWiki itself uses if duplicates exist). It returns `None` if missing.

### 5. Set or update an argument

```python
t.set_arg('age', '31')                      # update or create at end
t.set_arg('died', '2024', after='born')     # insert after |born=
t.set_arg('born', '1990', before='died')    # insert before |died=
t.set_arg('1', 'yes', positional=True)      # add positional value
t.set_arg('age', '31', preserve_spacing=True)  # mimic existing whitespace
```

Behaviour rules:

- If the argument already exists, its **value** is updated. `before`/`after`
  are ignored when updating.
- `positional` is only used when **creating** a new argument.
- `preserve_spacing=True` reads the surrounding whitespace pattern (mode
  across other args) and reuses it. Use it for nicely-formatted infoboxes;
  skip it for compact one-liners.

### 6. Add a positional argument

```python
t = wtp.parse("{{convert|10}}").templates[0]
t.set_arg('', 'km', positional=True)
str(t)   # '{{convert|10|km}}'
```

When name is empty and `positional` is unset, the library defaults to
`positional=True`.

### 7. Delete arguments

```python
t.del_arg('deprecated_field')   # removes ALL args with that name
```

There is no built-in `del_positional(n)`. To delete a positional arg:

```python
for arg in t.arguments:
    if arg.positional and arg.name == '2':
        del arg[:]              # deletes this argument from the buffer
        break
```

`del arg[:]` (or `del arg.string`) removes the node entirely, including its
leading `|`.

### 8. Has-arg checks

```python
t.has_arg('name')                  # name present (any value)
t.has_arg('status', 'deceased')    # exact-value match
```

Note that for keyword args `has_arg` strips whitespace before comparing both
the name and the value; for positional args the value is compared verbatim.

### 9. Clean up duplicate arguments

Two strategies, with different safety profiles:

```python
t.rm_dup_args_safe()        # only removes truly-redundant dupes
t.rm_dup_args_safe(tag='[[Category:Pages with duplicate args]]')

t.rm_first_of_dup_args()    # removes first occurrence; rendered output unchanged
```

Differences:

- **`rm_dup_args_safe()`** — only deletes a duplicate when both name and value
  match, OR when one of the duplicates is empty. Never loses data. If the
  duplicates have *different* non-empty values, both are kept; passing `tag`
  appends that tag to the surviving values for tracking.
- **`rm_first_of_dup_args()`** — removes the *first* occurrence. The rendered
  page is unchanged because MediaWiki uses the last value, but the source may
  lose hand-edited content silently. Use only when you're sure.

### 10. Pretty-print

```python
print(t.pformat())
print(t.pformat(indent='  ', remove_comments=True))
```

`pformat()` returns a string and does **not** mutate `t`. To replace the
template in the article with the pretty version:

```python
t[:] = t.pformat()
```

### 11. Nested templates

```python
parsed = wtp.parse("{{outer|x={{inner|y=1}}}}")
parsed.templates                  # [outer, inner]
parsed.templates[0].templates     # [inner]   (nested view excludes self)
parsed.templates[0].nesting_level # 0
parsed.templates[1].nesting_level # 1
```

### 12. Modify templates that contain `{{{params}}}`

If a template body uses parameters like `{{{1|}}}`, those are *not* templates
— they are `Parameter` objects. See `03-parameters.md`.

## Edge cases & gotchas

- **Order of arguments matters.** When iterating `t.arguments`, do not delete
  positional args in the middle and keep iterating — their `.name` (the
  position string) shifts. Iterate in reverse, or collect first.

  ```python
  for arg in reversed(t.arguments):
      if some_cond(arg):
          del arg[:]
  ```

- **`preserve_spacing` reads from existing args.** If the template has no
  args yet, `preserve_spacing` is silently ignored.
- **`set_arg` with `before`/`after` referencing a missing name** raises an
  `AttributeError` (it tries to call `.insert` on `None`). Always check
  `t.has_arg(...)` first if the anchor is uncertain.
- **`normal_name()` strips one language code prefix and one namespace prefix
  per call.** Template names like `{{en:fr:Foo}}` are not deeply unwrapped.
- **`t.name` includes whitespace.** When matching, compare via
  `t.normal_name()` or `.strip()`.
- **Values keep their whitespace.** `arg.value` of `| name = Alice ` is
  `' Alice '`, not `'Alice'`. Strip explicitly when comparing.
- **Setting `arg.positional = False`** raises `ValueError` (because the new
  name is unknown). Use `arg.name = 'something'` instead.
- **Comments inside `t.name`** are stripped only by `normal_name()`, not by
  `t.name`. They are part of the raw name.

## Recipes

### Recipe A: extract one infobox as a dict

```python
def extract_infobox(wikitext: str, infobox_name: str = None) -> dict | None:
    parsed = wtp.parse(wikitext)
    for t in parsed.templates:
        n = t.normal_name().lower()
        if (infobox_name and infobox_name.lower() in n) or \
           (not infobox_name and n.startswith('infobox')):
            return {a.name.strip(): a.value.strip()
                    for a in t.arguments if not a.positional}
    return None
```

### Recipe B: bulk-rename a parameter across an article

```python
def rename_arg(wikitext, template_name, old, new):
    parsed = wtp.parse(wikitext)
    for t in parsed.templates:
        if t.normal_name().lower() == template_name.lower():
            arg = t.get_arg(old)
            if arg is None:
                continue
            value = arg.value
            t.del_arg(old)
            t.set_arg(new, value)
    return str(parsed)
```

### Recipe C: delete a template entirely

```python
for t in parsed.templates:
    if t.normal_name() == 'Cleanup':
        del t[:]
```

### Recipe D: validate required fields

```python
REQUIRED = {'infobox person': ['name', 'birth_date']}

issues = []
for t in parsed.templates:
    name = t.normal_name().lower()
    needed = REQUIRED.get(name)
    if not needed:
        continue
    missing = [f for f in needed if not t.has_arg(f)]
    if missing:
        issues.append((name, missing))
```

### Recipe E: append a tracking category to incomplete templates

```python
for t in parsed.templates:
    if t.normal_name().lower() == 'infobox book' and not t.has_arg('isbn'):
        # write back at end of arguments
        t.set_arg('', '[[Category:Books missing ISBN]]', positional=True)
```

## See also

- `03-parameters.md` — the `{{{name|default}}}` syntax (different from args)
- `11-parser-functions.md` — `{{#if:...}}` shares the `Argument` machinery
- `12-tree-navigation.md` — how to find a parent template of a node
- `13-common-patterns.md` — more combined recipes
- `references/reference.md` — full signatures
