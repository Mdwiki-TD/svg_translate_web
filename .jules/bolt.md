## 2025-02-15 - [SQL Joins Over In-Memory Lookups]
**Learning:** Consolidating multiple database queries (e.g. querying a table and a view separately) into a single SQLAlchemy query using `outerjoin` is extremely efficient. It completely eliminates extra database round-trips, reduces in-memory hash map lookup construction overhead, and leverages database-level optimizations.
**Action:** When joining tables or views on slug/id, design a single SQLAlchemy query utilizing explicit `.outerjoin()` instead of executing multiple queries and merging result dictionaries in python.
