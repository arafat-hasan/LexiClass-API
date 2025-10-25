# Testing with Docker PostgreSQL

Since you're running PostgreSQL in Docker, use these commands instead of the standard PostgreSQL CLI tools.

## Quick Setup

```bash
cd LexiClass-API

# 1. Start Docker services (if not already running)
docker compose up -d db redis

# 2. Create test database
docker compose exec db psql -U lexiclass -c "CREATE DATABASE lexiclass_test;"

# 3. Verify database exists
docker compose exec db psql -U lexiclass -c "\l" | grep lexiclass_test

# 4. Install test dependencies
poetry install --with dev

# 5. Run tests
poetry run pytest tests/ -v
```

## Database Management Commands

### Create Test Database
```bash
docker compose exec db psql -U lexiclass -c "CREATE DATABASE lexiclass_test;"
```

### Drop Test Database (cleanup)
```bash
docker compose exec db psql -U lexiclass -c "DROP DATABASE IF EXISTS lexiclass_test;"
```

### List All Databases
```bash
docker compose exec db psql -U lexiclass -c "\l"
```

### Connect to Test Database (Interactive)
```bash
docker compose exec db psql -U lexiclass -d lexiclass_test
```

### Check Database Size
```bash
docker compose exec db psql -U lexiclass -c "SELECT pg_size_pretty(pg_database_size('lexiclass_test'));"
```

### View Tables in Test Database
```bash
docker compose exec db psql -U lexiclass -d lexiclass_test -c "\dt"
```

### Count Records in a Table
```bash
docker compose exec db psql -U lexiclass -d lexiclass_test -c "SELECT COUNT(*) FROM projects;"
```

## Troubleshooting

### Database Already Exists Error
If you see "database already exists", that's fine! The database is ready to use.

```bash
# To recreate from scratch:
docker compose exec db psql -U lexiclass -c "DROP DATABASE IF EXISTS lexiclass_test;"
docker compose exec db psql -U lexiclass -c "CREATE DATABASE lexiclass_test;"
```

### Connection Refused
Make sure PostgreSQL container is running:

```bash
docker compose ps

# If not running, start it:
docker compose up -d db
```

### Check PostgreSQL Logs
```bash
docker compose logs db
```

### Reset Everything
```bash
# Stop all containers
docker compose down

# Remove volumes (WARNING: deletes all data)
docker compose down -v

# Start fresh
docker compose up -d
```

## Alternative: Docker Exec psql

You can also create the database by entering PostgreSQL interactively:

```bash
# Enter PostgreSQL CLI
docker compose exec db psql -U lexiclass

# Then run:
CREATE DATABASE lexiclass_test;

# Exit with:
\q
```

## For CI/CD

In GitHub Actions or other CI environments, create the database in your workflow:

```yaml
- name: Create test database
  run: |
    docker compose up -d db
    sleep 5  # Wait for PostgreSQL to be ready
    docker compose exec -T db psql -U lexiclass -c "CREATE DATABASE lexiclass_test;"
```

## Environment Variables

Your `.env` file already has the correct settings:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=lexiclass
POSTGRES_PASSWORD=lexiclass
POSTGRES_DB=lexiclass
```

The tests will automatically use `lexiclass_test` instead of `lexiclass`.

## Summary

**Instead of:**
```bash
createdb lexiclass_test  # ❌ Won't work with Docker
```

**Use:**
```bash
docker compose exec db psql -U lexiclass -c "CREATE DATABASE lexiclass_test;"  # ✓ Works!
```
