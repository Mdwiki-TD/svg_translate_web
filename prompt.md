

You are a senior backend architect specializing in Python web systems.

Your task is to produce a comprehensive, production-grade technical plan to resolve MySQL error **1203 (max_user_connections exceeded)** in a Flask application currently using PyMySQL directly.

The solution must be based on **SQLAlchemy Engine for connection pooling (without requiring ORM models unless justified)**.

---

### Context

* Framework: Flask
* Current driver: PyMySQL
* Issue: Too many open MySQL connections (error 1203)
* Workload includes:

  * HTTP requests
  * Background tasks
  * Batch processing (e.g., processing ~700 files per job)
* Deployment may use Gunicorn with multiple workers.

---

### Requirements

1. Explain the root cause of error 1203 in this architecture.
2. Propose a clean architectural solution using SQLAlchemy connection pooling.
3. Provide:

   * Recommended pool configuration strategy.
   * Formula for calculating pool size based on workers and MySQL limits.
   * Safe lifecycle handling inside Flask (app context + teardown).
4. Include:

   * Example engine configuration
   * Example Flask integration
   * Example batch-processing pattern
5. Address:

   * pool_size
   * max_overflow
   * pool_recycle
   * pool_pre_ping
   * Worker count vs total connections math
6. Include monitoring and observability recommendations.
7. Include migration steps from raw PyMySQL to SQLAlchemy Engine.
8. Provide risk analysis and production hardening checklist.

---

### Output Rules

* Output must be structured in professional Markdown.
* Use clear section headings.
* Include code blocks with proper language tags.
* Do NOT include conversational text.
* The document must be implementation-ready.
* Save the final output to a file named:

```
mysql_connection_pooling_plan.md
```

The agent must generate the file directly and not just print the content.

Be precise, engineering-focused, and production-oriented.
