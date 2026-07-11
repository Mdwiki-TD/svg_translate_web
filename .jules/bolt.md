# Bolt's Performance Journal ⚡

## 2025-05-15 - Single-pass loops for API summary aggregation
**Learning:** In Flask API routes that return both a data list and multiple summary statistics (like `templates_list` and `owid_charts_list`), using separate `sum(1 for ...)` calls or multiple list comprehensions causes redundant iterations over the dataset. This leads to O(k*N) complexity where k is the number of summary fields.
**Action:** Refactor such routes to use a single manual loop that populates the result list and increments all summary counters simultaneously, reducing complexity to O(N). This is especially impactful for larger datasets where MediaWiki page lists or chart collections are processed.
