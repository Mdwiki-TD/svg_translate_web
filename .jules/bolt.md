# Bolt Performance Journal

This journal records critical learnings regarding application performance optimizations, specific bottlenecks, and lessons learned.

## 2026-03-01 - Avoid set() Reconstruction in Comprehensions
**Learning:** Re-instantiating a `set` from an iterable inside a list comprehension or generator expression creates an O(N*M) performance bottleneck, as the set is re-allocated and populated on every iteration.
**Action:** Always instantiate the `set` outside the list comprehension/generator and perform lookups against the pre-allocated set to achieve O(N + M) complexity.
