# Test Database Setup - Comprehensive Plan

**Goal**: Create isolated test database with automatic setup/teardown for safe, repeatable backend API testing.

---

## 📋 Overview

### Why Dedicated Test Database?

**Benefits:**
- ✅ Complete isolation from production data
- ✅ Safe to run destructive tests (DELETE, DROP, etc.)
- ✅ Realistic testing (same DB engine as production)
- ✅ Can test transactions, constraints, triggers
- ✅ Parallel test execution possible
- ✅ Automatic cleanup between test runs

**vs Transaction Rollback:**
- Transaction rollback is faster but can't test certain scenarios
- Test DB is slower but more complete coverage
- **Recommendation**: Use dedicated test DB for thorough testing

---

## 🔧 Step 1: Create Test Database

### Option A: Manual Creation (One-Time Setup)

**Connect as superuser:**
```bash
# If you have superuser access
psql -U postgres -h localhost -p 5432

# Or use existing admin account
psql -U <admin_user> -h localhost -p 5432
```

**Create test database and user:**
```sql
-- Create test database
CREATE DATABASE humanizer_test
    WITH
    OWNER = humanizer
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Grant permissions to humanizer user
GRANT ALL PRIVILEGES ON DATABASE humanizer_test TO humanizer;

-- Connect to test database
\c humanizer_test

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO humanizer;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO humanizer;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO humanizer;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES TO humanizer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO humanizer;
```

### Option B: Automated Creation Script

**File:** `backend/scripts/create_test_db.sh`
```bash
#!/bin/bash
# Create test database with pgvector extension

set -e

DB_NAME="humanizer_test"
DB_USER="humanizer"
DB_PASSWORD="humanizer"
DB_HOST="localhost"
DB_PORT="5432"

echo "🔧 Creating test database: $DB_NAME"

# Create database (requires superuser or CREATEDB privilege)
psql -U postgres -h $DB_HOST -p $DB_PORT <<EOF
-- Drop if exists (WARNING: Destructive!)
DROP DATABASE IF EXISTS $DB_NAME;

-- Create fresh database
CREATE DATABASE $DB_NAME
    WITH
    OWNER = $DB_USER
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

# Enable extensions
psql -U postgres -h $DB_HOST -p $DB_PORT -d $DB_NAME <<EOF
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

echo "✅ Test database created successfully!"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Connection: postgresql://$DB_USER:***@$DB_HOST:$DB_PORT/$DB_NAME"
```

**Make executable:**
```bash
chmod +x backend/scripts/create_test_db.sh
```

**Run once:**
```bash
cd backend
./scripts/create_test_db.sh
```

### Option C: Docker-Based Test Database (Recommended for CI/CD)

**File:** `backend/docker-compose.test.yml`
```yaml
version: '3.8'

services:
  postgres-test:
    image: ankane/pgvector:latest
    container_name: humanizer-test-db
    environment:
      POSTGRES_DB: humanizer_test
      POSTGRES_USER: humanizer
      POSTGRES_PASSWORD: humanizer
    ports:
      - "5433:5432"  # Use different port to avoid conflict
    volumes:
      - test-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U humanizer"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  test-db-data:
```

**Start test database:**
```bash
docker-compose -f docker-compose.test.yml up -d
```

**Stop and cleanup:**
```bash
docker-compose -f docker-compose.test.yml down -v
```

---

## 🧪 Step 2: Update Test Configuration

### Update conftest.py

**File:** `backend/tests/conftest.py`
```python
"""
Pytest configuration with dedicated test database.
"""

import sys
from pathlib import Path
import os

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient

from database.connection import get_db, Base
from main import app
from models.chunk_models import Collection, Message, Chunk, Media
from models.pipeline_models import TransformationJob

# Test database URL
# Option 1: Separate database on same port
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://humanizer:humanizer@localhost:5432/humanizer_test"
)

# Option 2: Docker container on different port
# TEST_DATABASE_URL = "postgresql+asyncpg://humanizer:humanizer@localhost:5433/humanizer_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """
    Create test database engine (session-scoped).

    Creates tables once per test session, drops them at the end.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables at session end
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session (function-scoped).

    Each test gets a fresh session. Tables are truncated between tests
    to ensure isolation.
    """
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

        # Cleanup: Truncate all tables after each test
        # This is faster than dropping/recreating tables
        await session.execute("TRUNCATE TABLE chunk_transformations CASCADE")
        await session.execute("TRUNCATE TABLE transformation_lineage CASCADE")
        await session.execute("TRUNCATE TABLE transformation_jobs CASCADE")
        await session.execute("TRUNCATE TABLE chunks CASCADE")
        await session.execute("TRUNCATE TABLE media CASCADE")
        await session.execute("TRUNCATE TABLE messages CASCADE")
        await session.execute("TRUNCATE TABLE collections CASCADE")
        await session.execute("TRUNCATE TABLE users CASCADE")
        await session.execute("TRUNCATE TABLE book_content_links CASCADE")
        await session.execute("TRUNCATE TABLE book_sections CASCADE")
        await session.execute("TRUNCATE TABLE books CASCADE")
        await session.commit()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# SAMPLE DATA FIXTURES (same as before)
# ============================================================================

@pytest.fixture
async def sample_collection(db_session: AsyncSession) -> Collection:
    """Create a sample collection for testing."""
    from uuid import uuid4
    from datetime import datetime, timezone

    collection = Collection(
        id=uuid4(),
        title="Test Collection",
        description="A test collection for unit testing",
        collection_type="conversation",
        source_platform="test",
        message_count=0,
        chunk_count=0,
        media_count=0,
        total_tokens=0,
        created_at=datetime.now(timezone.utc),
        import_date=datetime.now(timezone.utc),
        extra_metadata={"test": True}
    )

    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    return collection

# ... (rest of fixtures same as before)
```

---

## 🔄 Step 3: Migration Strategy

### Keep Test DB Schema in Sync

**Option A: Run Alembic Migrations**

**File:** `backend/scripts/migrate_test_db.sh`
```bash
#!/bin/bash
# Run Alembic migrations on test database

export DATABASE_URL="postgresql+asyncpg://humanizer:humanizer@localhost:5432/humanizer_test"

echo "🔄 Running migrations on test database..."
alembic upgrade head

echo "✅ Test database migrations complete!"
```

**Option B: Auto-Migrate Before Tests**

Add to `conftest.py`:
```python
@pytest.fixture(scope="session", autouse=True)
async def run_migrations():
    """Run Alembic migrations before test session starts."""
    import subprocess

    # Set environment variable for test database
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL

    # Run migrations
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        env=env,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Migration failed: {result.stderr}")

    yield
```

---

## 🚀 Step 4: Environment Variables

### Create Test Environment File

**File:** `backend/.env.test`
```bash
# Test Database Configuration
DATABASE_URL=postgresql+asyncpg://humanizer:humanizer@localhost:5432/humanizer_test

# Or for Docker-based test DB
# DATABASE_URL=postgresql+asyncpg://humanizer:humanizer@localhost:5433/humanizer_test

# Disable external API calls during testing
ANTHROPIC_API_KEY=test-key-not-used

# Test-specific settings
ENABLE_VECTOR_SEARCH=false  # Faster tests without embeddings
LOG_LEVEL=WARNING  # Less verbose output
```

### Load Test Environment in Pytest

**Update:** `backend/pytest.ini` or `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
env_files = [".env.test"]  # Requires pytest-env plugin
```

**Or manually in conftest.py:**
```python
import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(".env.test", override=True)
```

---

## 🧹 Step 5: Cleanup Strategies

### Strategy A: TRUNCATE Between Tests (Fastest)

**Pros:**
- Fast (no table recreation)
- Preserves table structure
- Resets sequences automatically with CASCADE

**Cons:**
- Must specify all tables manually
- Can't test DDL changes

**Implementation:** Already in conftest.py above

### Strategy B: DROP/CREATE Tables Per Test (Slowest)

**Pros:**
- Complete isolation
- Can test schema changes
- No manual table listing

**Cons:**
- Slow (~100ms per test)
- Re-creates indexes, constraints

**Implementation:**
```python
@pytest.fixture(scope="function")
async def db_session(engine):
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session_maker = async_sessionmaker(engine, ...)
    async with async_session_maker() as session:
        yield session
```

### Strategy C: Transaction Rollback (Medium Speed)

**Pros:**
- Fast
- Automatic cleanup
- No manual table listing

**Cons:**
- Can't test transaction-dependent code
- Nested transaction issues

**Implementation:**
```python
@pytest.fixture(scope="function")
async def db_session(engine):
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            session = AsyncSession(bind=connection, ...)
            yield session
            await transaction.rollback()
```

**Recommendation:** Start with TRUNCATE (Strategy A), move to Transaction Rollback if speed becomes an issue.

---

## 📊 Step 6: Performance Optimization

### Parallel Test Execution

**Install pytest-xdist:**
```bash
pip install pytest-xdist
```

**Run tests in parallel:**
```bash
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers
```

**Important:** Each worker needs isolated database session. Current fixture design supports this.

### Test Database Indexing

**Create indices after table creation:**
```python
@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Create additional test-specific indices
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_collections_created
            ON collections(created_at DESC);
        """)

    yield engine
    # ... cleanup
```

---

## 🔒 Step 7: Security & Best Practices

### Don't Commit Test Database Credentials

**In `.gitignore`:**
```
.env.test
scripts/*.local.sh
```

### Use Environment Variables

**For CI/CD:**
```yaml
# .github/workflows/test.yml
env:
  TEST_DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
```

### Separate Test Database Physically

**Production:** `humanizer` (port 5432)
**Test:** `humanizer_test` (port 5433 via Docker)

This prevents accidental production database access during tests.

---

## 🚦 Step 8: CI/CD Integration

### GitHub Actions Example

**File:** `.github/workflows/backend-tests.yml`
```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: ankane/pgvector:latest
        env:
          POSTGRES_DB: humanizer_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install poetry
          poetry install

      - name: Run tests
        env:
          TEST_DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/humanizer_test
        run: |
          cd backend
          poetry run pytest tests/ -v --cov=api --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📝 Step 9: Documentation & Developer Onboarding

### README Update

**Add to `backend/README.md`:**
```markdown
## Running Tests

### Setup (One-Time)

1. Create test database:
   ```bash
   ./scripts/create_test_db.sh
   ```

2. Or use Docker:
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/api/test_library_collections.py -v

# With coverage
pytest tests/ --cov=api --cov-report=html

# Parallel execution
pytest tests/ -n auto
```

### Cleanup Test Database

```bash
# Drop test database
psql -U postgres -c "DROP DATABASE humanizer_test;"

# Or stop Docker container
docker-compose -f docker-compose.test.yml down -v
```
```

---

## 🎯 Step 10: Validation Checklist

**Before committing test infrastructure:**

- [ ] Test database created successfully
- [ ] pgvector extension enabled
- [ ] Permissions granted to test user
- [ ] Test database URL in `.env.test`
- [ ] `.env.test` in `.gitignore`
- [ ] `conftest.py` uses test database
- [ ] Sample test passes: `pytest tests/api/test_library_collections.py::TestListCollections::test_list_collections_empty -v`
- [ ] Multiple tests pass: `pytest tests/api/test_library_collections.py -v`
- [ ] Database cleanup works (check tables truncated between tests)
- [ ] No production data accessed during tests
- [ ] Documentation updated (README.md)
- [ ] CI/CD workflow configured (if applicable)

---

## 🔄 Migration Path from Current State

### Current Situation
- Tests configured but using production database
- Tests fail because they expect empty database
- No isolation between tests

### Migration Steps

1. **Create test database** (choose one):
   - Run `./scripts/create_test_db.sh` (requires superuser)
   - Use Docker: `docker-compose -f docker-compose.test.yml up -d`

2. **Update conftest.py**:
   - Change `TEST_DATABASE_URL` from production to test DB
   - Keep TRUNCATE cleanup strategy

3. **Run first test**:
   ```bash
   pytest tests/api/test_library_collections.py::TestListCollections::test_list_collections_empty -v
   ```

4. **Verify isolation**:
   ```bash
   # Run test twice - both should pass
   pytest tests/api/test_library_collections.py -v
   pytest tests/api/test_library_collections.py -v
   ```

5. **Complete test suite**:
   - Create remaining test files
   - Run all tests: `pytest tests/api/ -v`

6. **Refactor with confidence**:
   - All tests pass → Safe to refactor
   - Refactor one file at a time
   - Re-run tests after each change

---

## 📈 Expected Timeline

| Task | Time | Dependencies |
|------|------|--------------|
| Create test database | 10 min | Superuser access or Docker |
| Update conftest.py | 5 min | Test database created |
| Create setup script | 15 min | None |
| Test first endpoint | 5 min | Updated conftest.py |
| Verify isolation | 10 min | First test passing |
| Document setup | 20 min | None |
| **Total** | **~1 hour** | |

---

## 🎓 Key Decisions to Make

### 1. Database Location

**Option A: Same PostgreSQL instance, different database**
- Pros: Simple, no new setup
- Cons: Requires CREATE DATABASE permission

**Option B: Docker container on different port**
- Pros: Complete isolation, easy cleanup
- Cons: Requires Docker installed

**Recommendation:** Option B (Docker) for development, Option A for CI/CD

### 2. Cleanup Strategy

**Option A: TRUNCATE tables**
- Speed: Fast (~10ms per test)
- Isolation: Good
- Complexity: Low

**Option B: Transaction rollback**
- Speed: Fastest (~5ms per test)
- Isolation: Excellent
- Complexity: Medium

**Recommendation:** TRUNCATE for now, optimize later if needed

### 3. Schema Migration

**Option A: Manual (run script before tests)**
- Control: High
- Automation: Low

**Option B: Auto-migrate (pytest fixture)**
- Control: Medium
- Automation: High

**Recommendation:** Option A for development, Option B for CI/CD

---

## 🚀 Next Actions

1. **Choose database setup method** (Manual vs Docker)
2. **Create test database**
3. **Update conftest.py with test DB URL**
4. **Run first test and verify**
5. **Document setup in README**
6. **Proceed with remaining test files**

**Ready to proceed?** Let me know which database setup option you prefer and I'll execute it.
