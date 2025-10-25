# Quick Start: API Testing Suite

## TL;DR

```bash
# 1. Start Docker services (if not running)
cd LexiClass-API
docker compose up -d db redis

# 2. Create test database (Docker method)
docker compose exec db psql -U lexiclass -c "CREATE DATABASE lexiclass_test;"

# 3. Install dependencies
poetry install --with dev

# 4. Run tests
poetry run pytest tests/ -v

# 5. Run the big test (1000 documents + indexing)
poetry run pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_create_project_add_1000_docs_and_index -v -s
```

> **Note**: If you have PostgreSQL installed locally (not Docker), you can use `createdb lexiclass_test` instead. See [DOCKER_SETUP.md](DOCKER_SETUP.md) for Docker-specific commands.

## What's Included

### Test Stack
- **pytest** - Test framework ✓
- **pytest-asyncio** - Async test support ✓
- **httpx** - Async HTTP client for API testing ✓
- **faker** - Realistic test data generation ← NEW
- **pytest-timeout** - Timeout control for long tests ← NEW

### Test Files Created

1. **`tests/conftest.py`**
   - Database fixtures with automatic cleanup
   - HTTP client configuration
   - Session management

2. **`tests/test_helpers.py`**
   - `DocumentGenerator` class
   - Generates realistic documents across 8 categories
   - Contextual content with category-specific vocabulary

3. **`tests/test_integration_full_workflow.py`**
   - Full workflow test: create project + 1000 docs + indexing
   - Smaller test: 100 documents (faster feedback)
   - Document generation quality test

## The Main Test

### test_create_project_add_1000_docs_and_index

This comprehensive integration test:

1. **Creates a project** via API
2. **Generates 1000 realistic documents** using Faker
   - 8 categories: Technology, Business, Health, Sports, Entertainment, Politics, Science, Education
   - Balanced distribution (~125 docs per category)
   - Realistic content (50-500 words per document)
   - Metadata: title, author, source, date

3. **Uploads documents in batches** of 100
   - Progress tracking
   - Error handling per batch

4. **Triggers indexing** job
   - Submits to Celery worker
   - Returns task ID

5. **Monitors progress**
   - Polls task status every 5 seconds
   - Timeout: 5 minutes
   - Displays progress updates

6. **Verifies results**
   - Index status: "valid"
   - All 1000 documents indexed
   - No failed documents
   - Project status updated

## Sample Output

```
=== Step 1: Creating project ===
✓ Project created: 1a988da4-3986-4e1d-8bcb-e2b4ac1a0f15
  Name: Test Project - 1000 Documents
  Status: active

=== Step 2: Generating 1000 documents ===
✓ Generated 1000 documents

Document distribution by category:
  Business: 125 documents
  Education: 125 documents
  Entertainment: 125 documents
  Health: 125 documents
  Politics: 125 documents
  Science: 125 documents
  Sports: 125 documents
  Technology: 125 documents

=== Step 3: Adding documents to project ===
  Uploading batch 1/10 (100 docs)... ✓ (100/1000 total)
  Uploading batch 2/10 (100 docs)... ✓ (200/1000 total)
  ...
  Uploading batch 10/10 (100 docs)... ✓ (1000/1000 total)

✓ Successfully added 1000 documents to project

=== Step 4: Verifying document count ===
✓ Project contains documents: 1000

=== Step 5: Triggering indexing ===
✓ Indexing task submitted: 3a7841f0-8397-45f2-9d17-363ecadf6dd4
  Status: pending
  Message: Indexing task submitted to worker

=== Step 6: Monitoring indexing progress ===
  [0s] Task state: STARTED
  [5s] Task state: STARTED
  [10s] Task state: SUCCESS

✓ Indexing completed successfully!
  Documents indexed: 1000
  Index path: /Users/arafat/lexiclass_data/.../indexes/index

=== Step 7: Verifying index status ===
✓ Index status: valid
  Total documents: 1000
  Indexed documents: 1000
  Pending documents: 0
  Failed documents: 0

=== Step 8: Final project status ===
✓ Project: Test Project - 1000 Documents
  Status: active
  Index status: valid
  Last indexed at: 2025-10-24T13:03:33

==================================================
✓ FULL WORKFLOW TEST PASSED!
==================================================
```

## Prerequisites

### 1. PostgreSQL Test Database

**If using Docker (recommended):**
```bash
# Start PostgreSQL container
docker compose up -d db

# Create test database
docker compose exec db psql -U lexiclass -c "CREATE DATABASE lexiclass_test;"

# Verify
docker compose exec db psql -U lexiclass -c "\l" | grep lexiclass_test
```

**If using local PostgreSQL:**
```bash
createdb lexiclass_test
# Or with psql
psql -c "CREATE DATABASE lexiclass_test;"
```

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for more Docker commands.

### 2. Redis Running

```bash
# Check if running
redis-cli ping

# Start if needed
redis-server
```

### 3. Worker Running (for integration tests)

```bash
cd LexiClass-Worker
source .venv/bin/activate
celery -A lexiclass_worker.celery worker --loglevel=INFO --queues=indexing,training,prediction
```

## Running Tests

### All tests
```bash
pytest tests/ -v
```

### Just the 1000-document test
```bash
pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_create_project_add_1000_docs_and_index -v -s
```

### Faster 100-document test
```bash
pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_smaller_workflow_100_docs -v -s
```

### With coverage
```bash
pytest tests/ --cov=lexiclass_api --cov-report=html
```

## Technology Recommendation Summary

**Best choice: pytest + httpx + Faker**

### Why this stack?

1. **pytest**
   - Industry standard Python testing framework
   - Excellent fixture system
   - Great plugin ecosystem
   - Already in your dependencies ✓

2. **httpx** (vs requests)
   - Better for async FastAPI testing
   - Modern API, similar to requests
   - Native async/await support
   - Already in your dependencies ✓

3. **Faker**
   - Generates realistic test data
   - Supports multiple locales and data types
   - Extensible and customizable
   - Perfect for generating 1000+ documents

4. **pytest-timeout**
   - Prevents tests from hanging
   - Essential for long-running operations
   - Configurable per test

### Alternative Considerations

**For load testing**: Consider **Locust**
```python
from locust import HttpUser, task

class APIUser(HttpUser):
    @task
    def create_documents(self):
        # Simulate concurrent users
        pass
```

**For BDD-style tests**: Consider **pytest-bdd**
```gherkin
Scenario: User adds 1000 documents
  Given a project exists
  When I upload 1000 documents
  Then the indexing should complete successfully
```

**For API contract testing**: Consider **schemathesis**
```python
import schemathesis

schema = schemathesis.from_uri("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_api(case):
    case.call_and_validate()
```

## Next Steps

1. ✓ Dependencies added to `pyproject.toml`
2. ✓ Test infrastructure created
3. ✓ Test helpers with realistic data generation
4. ✓ Comprehensive integration tests

**To install and run:**

```bash
cd LexiClass-API

# Install new dependencies
poetry install --with dev

# Create test database
createdb lexiclass_test

# Run a quick test
poetry run pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_document_generation_quality -v

# Run the full 1000-document test (requires worker running)
poetry run pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_create_project_add_1000_docs_and_index -v -s
```

## Tips

- **Start small**: Run the 100-document test first
- **Watch logs**: Keep worker logs visible during tests
- **Parallel testing**: Don't run multiple integration tests simultaneously (they share Redis/DB)
- **CI/CD**: See `tests/README.md` for GitHub Actions example
- **Debug mode**: Use `-v -s --tb=long` for detailed output

## Support

- Full documentation: `tests/README.md`
- Test helpers: `tests/test_helpers.py`
- Fixtures: `tests/conftest.py`
