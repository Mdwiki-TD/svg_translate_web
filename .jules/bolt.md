## 2026-07-22 - Hoist set instantiation out of list comprehensions

**Learning:** Instantiating a `set` inside a list comprehension or generator expression (e.g. `[x for x in list1 if x not in set(list2)]`) creates a set object on every iteration, inflating algorithm complexity from O(N + M) to O(N * M).
**Action:** Always extract set instantiations out of list comprehensions into a standalone local variable before filtering.
