# LexiClass API Test Suite

Comprehensive integration and unit tests for the LexiClass API.

## Test Structure

```
tests/
├── __init__.py                          # Package marker
├── conftest.py                          # Pytest fixtures and configuration
├── test_helpers.py                      # Test data generation utilities
├── test_integration_full_workflow.py    # Full workflow integration tests
└── README.md                            # This file
```

## Setup

### 1. Install Dependencies

```bash
# Using Poetry
poetry install --with dev

# Or using pip
pip install -e ".[dev]"
```

### 2. Add Required Dependencies

Make sure your `pyproject.toml` includes:

```toml
[tool.poetry.group.dev.dependencies]
pytest = ">=7.0.0"
pytest-asyncio = ">=0.23.0"
pytest-cov = ">=4.1.0"
pytest-timeout = ">=2.2.0"
httpx = ">=0.26.0"
faker = ">=20.0.0"
```

### 3. Create Test Database

The tests use a separate `lexiclass_test` database:

```bash
# PostgreSQL
createdb lexiclass_test

# Or using psql
psql -c "CREATE DATABASE lexiclass_test;"
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test

```bash
# Full workflow with 1000 documents
pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_create_project_add_1000_docs_and_index -v

# Smaller workflow with 100 documents (faster)
pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_smaller_workflow_100_docs -v

# Document generation quality test
pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_document_generation_quality -v
```

### Run with Coverage

```bash
pytest tests/ --cov=lexiclass_api --cov-report=html
```

### Run with Detailed Output

```bash
pytest tests/ -v -s
```

### Run with Timeout Control

```bash
# Override timeout for slow tests
pytest tests/ --timeout=900  # 15 minutes
```

## Test Fixtures

### `client` (AsyncClient)
- Async HTTP client for API testing
- Automatically handles database session
- Base URL: `http://test`

### `db_session` (AsyncSession)
- Database session for direct DB operations
- Automatic rollback after each test

### `api_url` (str)
- API base URL (e.g., `/api/v1`)

## Test Data Generation

### DocumentGenerator

The `DocumentGenerator` class creates realistic test documents with:

- **8 Categories**: Technology, Business, Health, Sports, Entertainment, Politics, Science, Education
- **Contextual Content**: Category-specific vocabulary and themes
- **Realistic Metadata**: Title, author, source, date
- **Configurable Length**: 50-500 words per document

#### Usage Examples

```python
from tests.test_helpers import DocumentGenerator

# Generate a single document
doc = DocumentGenerator.generate_document(
    category="Technology",
    min_words=100,
    max_words=200
)

# Generate multiple documents (balanced distribution)
docs = DocumentGenerator.generate_documents(
    count=1000,
    balanced=True  # Evenly distributed across categories
)

# Generate random distribution
docs = DocumentGenerator.generate_documents(
    count=500,
    balanced=False  # Random categories
)
```

## Integration Tests

### test_create_project_add_1000_docs_and_index

**Duration**: ~5-10 minutes
**Purpose**: Comprehensive end-to-end test

**Steps**:
1. Create a new project
2. Generate 1000 realistic documents across 8 categories
3. Upload documents in batches of 100
4. Trigger indexing job
5. Monitor indexing progress (polls every 5 seconds)
6. Verify index creation and document counts
7. Check final project status

**Expected Results**:
- All 1000 documents successfully added
- Indexing completes without errors
- Index status: "valid"
- No failed documents

### test_smaller_workflow_100_docs

**Duration**: ~1-2 minutes
**Purpose**: Quick validation test for development

**Steps**:
- Same workflow as above but with 100 documents
- Faster feedback loop for development

### test_document_generation_quality

**Duration**: < 1 second
**Purpose**: Validate test data generator

**Checks**:
- Document structure (content, label, metadata)
- Content length (50-500 words)
- Metadata completeness
- Category diversity

## Debugging Tests

### View Detailed Output

```bash
pytest tests/ -v -s --tb=long
```

### Run Single Test with Debug

```bash
pytest tests/test_integration_full_workflow.py::TestFullWorkflow::test_create_project_add_1000_docs_and_index -v -s
```

### Check Test Database

```bash
# Connect to test database
psql lexiclass_test

# View projects
SELECT id, name, status, index_status FROM projects;

# View document counts
SELECT project_id, COUNT(*) FROM documents GROUP BY project_id;
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: lexiclass_test
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with dev

      - name: Run tests
        run: poetry run pytest tests/ -v --cov
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/lexiclass_test
          CELERY_BROKER_URL: redis://localhost:6379/0
```

## Best Practices

1. **Isolate Tests**: Each test should be independent
2. **Use Fixtures**: Leverage pytest fixtures for setup/teardown
3. **Mock External Services**: Use mocks for external APIs (if needed)
4. **Test Data**: Use realistic test data via `DocumentGenerator`
5. **Async Tests**: Always mark async tests with `@pytest.mark.asyncio`
6. **Timeouts**: Set appropriate timeouts for long-running tests
7. **Cleanup**: Fixtures handle cleanup automatically

## Troubleshooting

### Test Database Connection Issues

```bash
# Check if database exists
psql -l | grep lexiclass_test

# Create if missing
createdb lexiclass_test

# Check connection
psql lexiclass_test -c "SELECT 1;"
```

### Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server
```

### Indexing Timeout

If indexing takes longer than expected:

1. Increase timeout in test: `@pytest.mark.timeout(900)`
2. Check worker logs for errors
3. Verify worker is running and processing jobs
4. Check Redis connection

### Import Errors

```bash
# Make sure package is installed in editable mode
pip install -e .

# Or with poetry
poetry install
```

## Performance Benchmarks

Typical test execution times (on M1 Mac, local environment):

- `test_document_generation_quality`: < 1s
- `test_smaller_workflow_100_docs`: ~60-120s
- `test_create_project_add_1000_docs_and_index`: ~300-600s

Times may vary based on:
- Hardware specifications
- Database performance
- Worker concurrency settings
- Network latency (if using remote services)
