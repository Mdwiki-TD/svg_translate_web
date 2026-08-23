---
name: qa-tester
description: Quality assurance and testing specialist. Use when asked to review test coverage, write new tests, identify regressions, create e2e tests, or improve testing practices.
---

# QA Tester

Ensure code quality through comprehensive testing. Focus on identifying gaps, preventing regressions, and building confidence in deployments.

## When to Use This Skill

Trigger when user asks to:

-   Review test coverage
-   Write tests for new or existing code
-   Identify potential regressions
-   Create end-to-end tests
-   Debug failing tests
-   Improve testing practices
-   Validate a feature works correctly
-   Check edge cases

## Testing Philosophy

**Principles:**

1. **Test behavior, not implementation** - Tests should survive refactoring
2. **Fast feedback** - Unit tests run in seconds, not minutes
3. **Deterministic** - Same input = same output, always
4. **Independent** - Tests don't depend on each other
5. **Readable** - Tests are documentation

**Testing pyramid:**

```
        /\
       /  \     E2E Tests (few, slow, high confidence)
      /----\
     /      \   Integration Tests (some, medium speed)
    /--------\
   /          \ Unit Tests (many, fast, focused)
  --------------
```

## Current Test Inventory

### Existing Tests

| File                                   | Type        | Coverage Area                 |
| -------------------------------------- | ----------- | ----------------------------- |
| `test_greenhouse_title_filter_unit.py` | Unit        | Title pattern matching        |
| `test_greenhouse_scraper_filtered.py`  | Unit        | Scraper filtering logic       |
| `test_e2e_greenhouse_filtered.py`      | E2E         | Full Greenhouse pipeline      |
| `test_db_upsert.py`                    | Integration | Database upsert patterns      |
| `test_incremental_pipeline.py`         | Integration | Incremental processing        |
| `test_resume_capability.py`            | Integration | Pipeline resume feature       |
| `test_location_extractor.py`           | Unit        | Location parsing              |
| `eval_gemini.py`                       | Evaluation  | LLM accuracy (not regression) |

### Coverage Gaps

**Untested modules (HIGH PRIORITY):**

| Module                   | Risk   | Suggested Tests                                  |
| ------------------------ | ------ | ------------------------------------------------ |
| `classifier.py`          | High   | JSON parsing, error handling, provider switching |
| `agency_detection.py`    | Medium | Blocklist matching, pattern detection            |
| `lever_fetcher.py`       | Medium | API responses, pagination, error handling        |
| `skill_family_mapper.py` | Low    | Mapping accuracy, unknown skill handling         |
| `job_family_mapper.py`   | Low    | Subfamily to family mapping                      |

**Untested scenarios:**

-   Malformed LLM responses
-   Network failures during scraping
-   Supabase connection errors
-   Rate limit handling
-   Concurrent pipeline runs

## Test Writing Guide

### Unit Test Template

```python
"""Tests for [module_name].py"""
import pytest
from unittest.mock import Mock, patch
from pipeline.[module] import function_under_test


class TestFunctionUnderTest:
    """Tests for function_under_test()"""

    def test_happy_path(self):
        """Should [expected behavior] when [conditions]"""
        # Arrange
        input_data = {...}
        expected = {...}

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected

    def test_edge_case_empty_input(self):
        """Should handle empty input gracefully"""
        result = function_under_test({})
        assert result is None  # or appropriate default

    def test_error_handling(self):
        """Should raise ValueError when [invalid condition]"""
        with pytest.raises(ValueError, match="expected message"):
            function_under_test(invalid_input)


class TestIntegrationScenario:
    """Integration tests for [scenario]"""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        with patch('pipeline.db_connection.get_supabase_client') as mock:
            mock.return_value = Mock()
            yield mock

    def test_full_flow(self, mock_db):
        """Should process job through full pipeline"""
        # Test implementation
        pass
```

### E2E Test Template

```python
"""End-to-end tests for [feature]"""
import pytest
from unittest.mock import patch


@pytest.mark.e2e
@pytest.mark.slow
class TestE2EFeature:
    """E2E tests - run with: pytest -m e2e"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup and teardown for E2E tests"""
        # Setup: create test data
        yield
        # Teardown: clean up test data

    def test_complete_pipeline_run(self):
        """Should successfully process jobs from source to database"""
        # Full pipeline execution test
        pass
```

## Testing Checklist

### For New Features

-   [ ] Unit tests for new functions
-   [ ] Edge cases identified and tested
-   [ ] Error conditions tested
-   [ ] Integration with existing code tested
-   [ ] Documentation updated

### For Bug Fixes

-   [ ] Regression test added (test that would have caught the bug)
-   [ ] Related edge cases checked
-   [ ] Fix doesn't break existing tests

### For Refactoring

-   [ ] Existing tests still pass
-   [ ] No decrease in coverage
-   [ ] Tests updated if interfaces changed

## Test Patterns for This Codebase

### Testing LLM Integration (classifier.py)

```python
def test_classifier_handles_malformed_json():
    """Should handle LLM returning invalid JSON"""
    with patch('pipeline.classifier.call_gemini') as mock_llm:
        mock_llm.return_value = "This is not JSON"

        result = classify_job("Test job description")

        assert result is None  # or error dict
        # Verify error was logged

def test_classifier_provider_fallback():
    """Should fall back to Claude when Gemini fails"""
    with patch('pipeline.classifier.call_gemini') as mock_gemini:
        mock_gemini.side_effect = Exception("API Error")

        with patch('pipeline.classifier.call_claude') as mock_claude:
            mock_claude.return_value = valid_response

            result = classify_job("Test job")

            mock_claude.assert_called_once()
```

### Testing Scrapers

```python
def test_greenhouse_scraper_handles_empty_page():
    """Should return empty list when no jobs found"""
    with patch('scrapers.greenhouse.greenhouse_scraper.fetch_page') as mock:
        mock.return_value = "<html><body>No jobs</body></html>"

        result = scrape_company("test-company")

        assert result == []

def test_greenhouse_scraper_pagination():
    """Should fetch all pages of results"""
    # Mock multiple pages
    pass

def test_lever_api_rate_limiting():
    """Should handle 429 responses with backoff"""
    pass
```

### Testing Database Operations

```python
@pytest.fixture
def test_db():
    """Use test database or mock"""
    # Option 1: Separate test database
    # Option 2: Mock Supabase client
    pass

def test_upsert_new_job(test_db):
    """Should insert new job and return ID"""
    pass

def test_upsert_existing_job(test_db):
    """Should update existing job, not duplicate"""
    pass

def test_deduplication_by_hash(test_db):
    """Should detect duplicate by job_hash"""
    pass
```

### Testing Configuration

```python
def test_agency_blacklist_loads():
    """Should load agency blacklist YAML"""
    from config import load_agency_blacklist

    blacklist = load_agency_blacklist()

    assert isinstance(blacklist, list)
    assert len(blacklist) > 0

def test_job_family_mapping_complete():
    """All subfamilies should map to a family"""
    from pipeline.job_family_mapper import SUBFAMILY_TO_FAMILY

    for subfamily, family in SUBFAMILY_TO_FAMILY.items():
        assert family in ['data', 'product', 'delivery', 'out_of_scope']
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_classifier.py -v

# Run tests matching pattern
pytest tests/ -k "test_greenhouse" -v

# Run only unit tests (fast)
pytest tests/ -m "not e2e" -v

# Run with coverage
pytest tests/ --cov=pipeline --cov-report=html

# Run only failed tests from last run
pytest tests/ --lf
```

## Test Configuration

**pytest.ini or pyproject.toml:**

```ini
[pytest]
markers =
    e2e: End-to-end tests (slow)
    integration: Integration tests
    unit: Unit tests (fast)
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

## Output Format

When reviewing tests, produce:

```markdown
## Test Coverage Report

**Date:** [Date]
**Scope:** [What was reviewed]

### Coverage Summary

| Module                | Current | Target | Gap    |
| --------------------- | ------- | ------ | ------ |
| classifier.py         | 0%      | 80%    | HIGH   |
| agency_detection.py   | 0%      | 70%    | MEDIUM |
| db_connection.py      | 40%     | 70%    | MEDIUM |
| location_extractor.py | 85%     | 80%    | OK     |

### Tests Needed

#### High Priority

1. **[Module/Function]**
    - Scenario: [what to test]
    - Type: Unit/Integration/E2E
    - Risk if untested: [consequence]

#### Medium Priority

1. **[Module/Function]**
    - Scenario: [what to test]

### Existing Test Issues

1. **[Test file]**
    - Issue: [flaky/slow/outdated]
    - Fix: [recommendation]

### Recommended Test Structure
```

tests/
+-- unit/
| +-- test_classifier.py
| +-- test_agency_detection.py
+-- integration/
| +-- test_db_operations.py
| +-- test_pipeline_flow.py
+-- e2e/
| +-- test_full_pipeline.py
+-- fixtures/
+-- sample_jobs.json
+-- mock_responses/

```

```

## Key Files to Reference

-   `tests/TESTING_GUIDE.md` - Existing test documentation
-   `tests/fixtures/` - Test data and mocks
-   `pytest.ini` or `pyproject.toml` - Test configuration
-   `.github/workflows/` - CI test configuration (if exists)
