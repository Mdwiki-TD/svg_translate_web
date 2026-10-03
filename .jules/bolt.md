## 2026-09-29 - Avoid instantiating `set()` inside list comprehensions

**Learning:** Instantiating a `set()` inside a list comprehension predicate (e.g. `[x for x in list_a if x not in set(list_b)]`) re-creates the set on every iteration over `list_a`, inflating complexity from O(N + M) to O(N * M) and causing excessive temporary memory allocations.

**Action:** Always hoist `set()` construction outside of list comprehensions or loop bodies into a local variable (e.g. `set_b = set(list_b)`) before filtering or iterating.
