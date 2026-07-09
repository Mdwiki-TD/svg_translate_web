## 2025-05-13 - Consolidating multiple list traversals in API routes
**Learning:** In Flask API routes providing summary metrics alongside data lists, the common pattern of using multiple `sum(1 for x in list if condition)` calls creates O(M*N) overhead (where M is the number of metrics). This can be significantly optimized to O(N) by using a single manual loop.
**Action:** Always check for redundant list traversals when an API response includes multiple summary counters and a data list.
