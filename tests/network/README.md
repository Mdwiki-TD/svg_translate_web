# Network Tests

This directory contains **real integration tests** that make live HTTP requests to Wikimedia servers. They are not mocked.

## What These Tests Do

The tests exercise `MwClientPage` against actual MediaWiki APIs to verify that the wrapper behaves correctly end-to-end, including authentication, rate-limiting, redirect resolution, and error handling.

## Sites Used

| Property         | Domain                       | Purpose                                         |
| ---------------- | ---------------------------- | ----------------------------------------------- |
| `self.site`      | `commons.wikimedia.org`      | Read-only / query tests (exists, redirects)     |
| `self.test_site` | `test-commons.wikimedia.org` | Write tests (create, edit, move) — safe sandbox |

Write operations (create, edit, move) **must** target `self.test_site` only. Never write to `commons.wikimedia.org` in tests.

## Running

These tests are marked with `@pytest.mark.network` and are skipped by default.

```bash
# Run only network tests
pytest -m network

# Run everything including network tests
pytest --run-network
```

Add `--run-network` to your `pytest.ini` or `conftest.py` to enable them in CI selectively.

## Authentication

Write tests require a bot account on `test-commons.wikimedia.org`. Set the following environment variables before running:

```
MW_TEST_USERNAME=YourBot@BotName
MW_TEST_PASSWORD=your_bot_password
```

If these variables are absent the write-test classes are skipped automatically.

## Shared Site Fixture

`shared_site_resource(domain)` is decorated with `@functools.lru_cache` so the `mwclient.Site` connection is created once per domain per test session, not once per test. This avoids hammering the login endpoint and keeps the suite fast.

## Test Class Layout

| Class                   | Site used        | Operations covered                               |
| ----------------------- | ---------------- | ------------------------------------------------ |
| `TestLoadPage`          | both             | valid title, invalid title, missing page         |
| `TestExists`            | `self.site`      | existing page, non-existing page                 |
| `TestGetRedirectTarget` | `self.site`      | redirect page, non-redirect page                 |
| `TestIsRedirect`        | `self.site`      | redirect, non-redirect                           |
| `TestCreate`            | `self.test_site` | create new page, create duplicate (error)        |
| `TestEdit`              | `self.test_site` | edit existing page, edit missing page (nocreate) |
| `TestMove`              | `self.test_site` | move page, move missing page (error)             |
| `TestMwClientPage`      | both             | full round-trip smoke tests                      |

## Cautions

-   Do not run write tests against production wikis.
-   Test pages created on `test-commons.wikimedia.org` are periodically purged by Wikimedia — do not rely on them persisting between runs.
-   Rate-limiting is real here; the retry logic in `_with_retry` will be exercised if you run the suite in parallel. Prefer sequential execution (`-p no:xdist`).
