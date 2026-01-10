You are a codebase refactoring/testing agent.

1. Search the repository for every file under `tests/` whose entire content is exactly:

```
"""
Tests
# TODO: Implement test
"""
```

2. For each matched file:

* Keep the file location unchanged.
* Replace its content with a valid pytest module containing **placeholder tests**.

3. Determine the corresponding source module:

* Map `tests/<path>/test_*.py` to `src/<path>/*.py` (mirror folder structure).
* Import every function/class from the corresponding source file (or import the module and reference symbols).

4. For **each function/class** found in that source file, create **one pytest placeholder test**:

* Name: `test_<symbol_name>()`
* Decorate with:

```
@pytest.mark.skip(reason="Pending write")
```

* Body must contain:

```
# TODO: Implement test
pass
```

5. The test file must include required imports, example:

```
import pytest
from <correct.import.path> import <all_symbols>
```

6. Ensure the test file reflects its current path and target source module correctly (no wrong imports).
7. Do not add real assertions; only placeholders.
8. Keep formatting clean and PEP8-compliant.


### Agent Notice / Constraint

**Important constraint:**
When generating placeholder tests for a source file, create tests **ONLY** for symbols declared in that file that start with:

* `def `
* `class `

Meaning:

* Parse the source file and extract **only top-level** `def` and `class` declarations.
* **Ignore everything else**, including:

  * imported functions/classes
  * constants/variables
  * nested functions/classes
  * assignments
  * `if __name__ == "__main__":`
  * comments and docstrings

For each extracted `def` / `class`, generate exactly **one** placeholder test function.

Example extraction rule:

* Count only lines that begin (after optional indentation at column 0) with `def ` or `class `.


Output: apply changes directly to the files.

