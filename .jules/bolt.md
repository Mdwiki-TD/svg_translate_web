# Bolt's Performance Journal - Critical Learnings

## 2025-07-10 - [Optimization of API Route Aggregations]
**Learning:** In Flask API routes that return both a data list and summary statistics, using multiple `sum(1 for ...)` calls or separate list comprehensions causes multiple O(N) iterations over the same dataset. For large datasets like OWID charts (which can grow to thousands of entries), this leads to measurable overhead.
**Action:** Always use a single manual loop to build the result list and increment all summary counters simultaneously. This reduces complexity from O(M*N) to O(N), where M is the number of summary statistics.
