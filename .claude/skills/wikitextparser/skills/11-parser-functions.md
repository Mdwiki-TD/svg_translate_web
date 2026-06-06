---
name: wikitextparser-parser-functions
description: >
  Inspect MediaWiki parser functions like {{#if:...}}, {{#switch:...}},
  {{#ifeq:...}}, {{#expr:...}}, magic words, and template-with-colon-syntax
  invocations. Covers the ParserFunction class, name vs arguments, the
  shared SubWikiTextWithArgs machinery with Template, and the important
  fact that wikitextparser DOES NOT evaluate parser functions.
applies_to:
  - "ParserFunction"
  - "{{#if:}}"
  - "{{#switch:}}"
  - "{{#ifeq:}}"
  - "{{#ifexist:}}"
  - "{{#expr:}}"
  - "{{ucfirst:}}"
  - "{{lc:}}"
---

# 11 — Parser Functions (`{{#if:...}}`, magic words)

> Open this file when you need to inspect or rewrite parser functions —
> the `{{#name:arg1|arg2|...}}` and magic-word-style `{{ucfirst:x}}`
> invocations.

## When to use this file

Use this file for:

- Listing all `{{#if:}}`/`{{#switch:}}`/etc. on a page.
- Reading the test expression and its branches.
- Modifying a default branch of a `{{#switch:}}`.

For ordinary `{{Template|args}}` calls, see `02-templates.md`.

## Mental model

Parser functions look like templates but use a colon (`:`) to separate the
function name from its first argument:

```text
{{ #if:  CONDITION  | THEN | ELSE }}
   ^^^   ^^^^^^^^^   ^^^^   ^^^^
   name  args[0]     args[1] args[2]
```

`ParserFunction` shares its parsing machinery (`SubWikiTextWithArgs`) with
`Template`, so it has the **same `name`, `arguments`, `nesting_level`, and
`get_lists()` API**. Differences:

- The first argument starts with `:` (after the name) instead of `|`.
- The name typically begins with `#` (e.g. `#if`, `#switch`) but parser
  functions implementing magic words (`ucfirst`, `lc`, `formatnum`) do not.

> **Important:** `wikitextparser` does **not** evaluate parser functions.
> It only gives you the parse tree. To get a result, expand server-side
> via the MediaWiki API (`?action=expandtemplates`) or use Pywikibot.

## Quick reference

| Attribute / method                                 | Description                                    |
| -------------------------------------------------- | ---------------------------------------------- |
| `parsed.parser_functions`                          | All parser functions (recursive)               |
| `pf.name`                                          | Function name (often starts with `#`)          |
| `pf.arguments`                                     | `list[Argument]` (first one is the condition)  |
| `pf.nesting_level`                                 | 0 = top-level; +1 per enclosing template/PF    |
| `pf.parser_functions`                              | Nested parser functions (excludes self)        |
| `pf.get_lists(pattern=...)`                        | Lists across all arguments                     |

The `Argument` class is identical to the one used by `Template`. See
`02-templates.md` for its full surface (`name`, `value`, `positional`).

## Step by step

### 1. List all parser functions

```python
parsed = wtp.parse("Result: {{#if:{{{x|}}}|yes|no}}")
for pf in parsed.parser_functions:
    print(pf.name, '->', [a.value for a in pf.arguments])
# #if  ->  ['{{{x|}}}', 'yes', 'no']
```

The first argument's value contains the condition, including any leading or
trailing whitespace from the source.

### 2. Distinguish parser functions from templates

`Template` has its first separator as `|`, `ParserFunction` as `:`. The
library disambiguates automatically — but a template called *with* a
colon-prefixed name (interwiki/namespace) is still a Template.

```python
parsed = wtp.parse("{{en:Foo}}")
parsed.templates              # one Template (because there's no | inside)
parsed.parser_functions       # []
```

```python
parsed = wtp.parse("{{lc:HELLO}}")
parsed.parser_functions       # one ParserFunction with name='lc'
parsed.templates              # []
```

`{{lc:...}}` is a magic-word parser function (lower-case). It does not start
with `#` because magic words historically don't.

### 3. Inspect arguments of `{{#switch:}}`

```python
parsed = wtp.parse("""
{{#switch: {{{type|}}}
 | book   = bk
 | film   = mv
 | song   = sg
 | #default = ??
}}
""")
pf = parsed.parser_functions[0]
pf.name              # '#switch'
for a in pf.arguments:
    print(repr(a.name), '=>', repr(a.value))
```

In `#switch`, each `key=value` pair is an `Argument` with `positional == False`,
exactly like a template's keyword arg. The very first argument is the
expression being switched on (positional).

### 4. Modify a branch of `{{#switch:}}`

```python
for pf in parsed.parser_functions:
    if pf.name.strip() == '#switch':
        for arg in pf.arguments:
            if arg.name.strip() == '#default':
                arg.value = 'unknown'
```

### 5. Negate an `{{#if:}}` (swap then/else)

```python
for pf in parsed.parser_functions:
    if pf.name.strip() == '#if':
        args = pf.arguments
        if len(args) >= 3:
            args[1].value, args[2].value = args[2].value, args[1].value
```

### 6. Replace a parser function call wholesale

```python
for pf in parsed.parser_functions:
    if pf.name.strip() == '#if' and pf.arguments[0].value.strip() == '':
        # `{{#if:|then|else}}` always picks "else"
        pf[:] = pf.arguments[2].value if len(pf.arguments) > 2 else ''
```

This is essentially manual evaluation; for non-trivial cases prefer
server-side expansion.

### 7. Walk lists or templates inside a parser function

```python
for pf in parsed.parser_functions:
    nested_templates = pf.templates       # all templates inside any branch
    lists_in_branches = pf.get_lists()    # convenience across all arguments
```

### 8. Nesting

```python
parsed.parser_functions[0].nesting_level  # 0
# Inside another template/parser function: 1, 2, ...
```

`nesting_level` counts both template and parser-function ancestors.

## Edge cases & gotchas

- **No evaluation.** `wtp` will *never* compute the result of `{{#if:}}` or
  `{{#expr:}}`. Treat the AST as static. Use the MediaWiki API for
  expansion if you need rendered output.
- **Magic words without arguments** like `{{NAMESPACE}}` or
  `{{CURRENTYEAR}}` look like templates with no arguments. They appear in
  `parsed.templates`, not `parsed.parser_functions`.
- **Behavior switches** like `__NOTOC__` are not parsed — they remain in
  the surrounding text.
- **Parser functions can contain templates**, and templates can contain
  parser functions. Always use `parsed.parser_functions` and
  `parsed.templates` together if you want both.
- **The argument with `name == '1'`** (or any positional) carries the
  *condition* in `#if` / `#ifeq` / `#switch`. Use the position string,
  not the value, to identify it.
- **Whitespace inside arguments is meaningful** for parser functions
  (especially conditions). Always `.strip()` when comparing values.
- **`pf.name` includes leading whitespace** if the source had any; use
  `.strip()` before comparing to `'#if'`.

## Recipes

### Recipe A: list every condition tested in `{{#if:}}`/`{{#ifeq:}}`

```python
def list_conditions(parsed) -> list[str]:
    out = []
    for pf in parsed.parser_functions:
        n = pf.name.strip()
        if n == '#if' and pf.arguments:
            out.append(pf.arguments[0].value.strip())
        elif n == '#ifeq' and len(pf.arguments) >= 2:
            out.append(f'{pf.arguments[0].value.strip()} == {pf.arguments[1].value.strip()}')
    return out
```

### Recipe B: swap default and main case in every `{{#switch:}}`

```python
for pf in parsed.parser_functions:
    if pf.name.strip() != '#switch':
        continue
    default = next((a for a in pf.arguments if a.name.strip() == '#default'), None)
    if default is None or len(pf.arguments) < 2:
        continue
    # Swap with the first keyed arg
    first_keyed = next((a for a in pf.arguments[1:] if not a.positional and a.name.strip() != '#default'), None)
    if first_keyed:
        first_keyed.value, default.value = default.value, first_keyed.value
```

### Recipe C: detect parser functions used by name

```python
from collections import Counter
counts = Counter(pf.name.strip() for pf in parsed.parser_functions)
```

### Recipe D: check whether any branch of `{{#if:}}` is empty

```python
for pf in parsed.parser_functions:
    if pf.name.strip() != '#if':
        continue
    branches = pf.arguments[1:]
    empties = [i for i, a in enumerate(branches) if not a.value.strip()]
    if empties:
        print(f'#if has empty branch(es): {empties}')
```

## See also

- `02-templates.md` — `Template` and `Argument` (shared with parser functions)
- `01-wikitext-basics.md` — `plain_text(replace_parser_functions=...)`
- `references/reference.md` — full ParserFunction API
