# Infrastructure Improvements Summary

## Problem Statement

### Critical Issue Found
```bash
$ python -c "import sentence_transformers"
ImportError: cannot import name 'cached_download' from 'huggingface_hub'
```

**Impact**: Madhyamaka detection silently falling back to regex-only mode (mathematically unsound) because `sentence-transformers` is broken.

**Root Cause**: Dependency version conflict between `sentence-transformers==2.2.2` and newer `huggingface_hub` API.

**Old Behavior**: Print warning, degrade to regex mode, continue serving requests with incorrect results.

**Required Behavior**: **FAIL FAST**. Don't start the service with broken dependencies.

## Solutions Implemented

### 1. Poetry for Dependency Management

**Created**: `backend/pyproject.toml`

**Benefits**:
- Lock file (`poetry.lock`) ensures reproducible environments
- Dependency resolver prevents version conflicts
- Separate dev/production dependencies
- Better than pip for complex dependency trees

**Migration**:
```bash
cd backend
rm -rf venv/
poetry install
poetry shell
```

### 2. Fail-Fast Dependency Validation

**Created**: `backend/core_dependencies.py`

**Modified**: `backend/main.py` (added validation at import time)

**Behavior**:
```python
# At startup, BEFORE FastAPI initializes
validate_dependencies()  # Raises DependencyError if anything broken
```

**Output on failure**:
```
======================================================================
CRITICAL DEPENDENCY VALIDATION FAILED
======================================================================

[ERROR 1] sentence-transformers: BROKEN_INSTALLATION
  Details: cannot import name 'cached_download'
  Fix: poetry install --sync
  Impact: Madhyamaka detection will fail - semantic embeddings broken

======================================================================
SERVICE STARTUP ABORTED - FIX DEPENDENCIES AND RESTART
======================================================================
```

**No more silent fallbacks. No more degraded mode.**

### 3. Alembic for Database Migrations

**Created**:
- `backend/alembic.ini` - Configuration
- `backend/alembic/env.py` - Migration environment (async-aware)
- `backend/alembic/script.py.mako` - Migration template
- `backend/alembic/versions/` - Migration scripts directory

**Modified**:
- `backend/database/connection.py` - Deprecated `create_all()`, added warning

**Usage**:
```bash
# Create migration after model changes
alembic revision --autogenerate -m "Add column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check status
alembic current
```

**Benefits**:
- Every schema change is version-controlled
- Migrations can be reviewed before applying
- Rollback capability for production
- No more schema drift between environments
- Team collaboration on schema changes

## Testing the Migration

### Step 1: Install Poetry Dependencies

```bash
cd /Users/tem/humanizer-agent/backend

# Remove broken venv
rm -rf venv/

# Install with Poetry
poetry install

# This will:
# - Create new virtualenv in ~/.cache/pypoetry/virtualenvs/
# - Install sentence-transformers 2.3.0+ (fixes huggingface_hub issue)
# - Generate poetry.lock
```

### Step 2: Test Dependency Validation

```bash
# Activate Poetry shell
poetry shell

# Try to start server - should validate dependencies first
python main.py
```

**Expected output**:
```
======================================================================
VALIDATING CRITICAL DEPENDENCIES
======================================================================
✓ sentence-transformers: OK
✓ asyncpg (PostgreSQL driver): OK
✓ pgvector: OK
✓ anthropic: OK
======================================================================
ALL CRITICAL DEPENDENCIES VALIDATED ✓
======================================================================
Starting Humanizer Agent API
...
```

**If validation fails**, service won't start (as intended).

### Step 3: Create Initial Alembic Migration

**IMPORTANT**: Choose one option based on your database state.

#### Option A: Fresh Start (Drop Existing DB)

```bash
cd /Users/tem/humanizer-agent/backend

# WARNING: This destroys all data
psql -U humanizer -d postgres -c "DROP DATABASE IF EXISTS humanizer;"
psql -U humanizer -d postgres -c "CREATE DATABASE humanizer;"
psql -U humanizer -d humanizer -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Generate initial migration from models
alembic revision --autogenerate -m "Initial schema"

# Review the generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Verify tables created
psql -U humanizer -d humanizer -c "\dt"
```

#### Option B: Keep Existing Data (Baseline Migration)

```bash
cd /Users/tem/humanizer-agent/backend

# Generate baseline migration (shows what WOULD be created)
alembic revision --autogenerate -m "Baseline from existing schema"

# Review alembic/versions/<revision>_baseline.py
# Should show operations for all existing tables

# Mark as applied WITHOUT running (DB already has these tables)
alembic stamp head

# Future migrations will apply incrementally from here
```

### Step 4: Verify Madhyamaka Detection Works

```bash
# Start server
poetry run python main.py

# In another terminal, test detection endpoint
curl -X POST http://localhost:8000/api/madhyamaka/detect/eternalism \
  -H "Content-Type: application/json" \
  -d '{"content": "This is absolutely essential and always true"}'
```

**Expected response**:
```json
{
  "eternalism_detected": true,
  "confidence": 0.78,
  "scoring_method": "semantic_primary",  // NOT "regex_fallback"
  "semantic_score": 0.78,
  "regex_score": 0.65,
  "metric_space": "embedding_cosine_similarity"
}
```

## Files Created

```
backend/
├── pyproject.toml              # Poetry configuration
├── poetry.lock                 # Locked dependencies (auto-generated)
├── core_dependencies.py        # Fail-fast validation
├── alembic.ini                 # Alembic config
├── alembic/
│   ├── env.py                  # Migration environment (async)
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration scripts
├── MIGRATION_GUIDE.md          # Step-by-step guide
└── INFRASTRUCTURE_SUMMARY.md   # This file
```

## Files Modified

```
backend/
├── main.py                     # Added validate_dependencies() call
└── database/connection.py      # Deprecated create_all(), added warning
```

## Files to Delete (After Migration)

```
backend/
├── requirements.txt            # Replaced by pyproject.toml
└── venv/                       # Replaced by Poetry virtualenv
```

## Next Steps

1. **Test the migration** (follow Step 1-4 above)
2. **Document changes in ChromaDB** (once tested)
3. **Update start.sh** to use `poetry run python main.py`
4. **Commit to git**:
   - Add `poetry.lock` (important!)
   - Add `alembic/versions/*.py` (migrations)
   - Add new infrastructure files
5. **Update CI/CD** to use Poetry

## Success Criteria

✅ `poetry install` completes without errors
✅ `python -c "import sentence_transformers"` works
✅ Server starts with dependency validation passing
✅ Madhyamaka detection uses `semantic_primary` (not `regex_fallback`)
✅ Alembic migrations apply cleanly
✅ Can rollback migrations with `alembic downgrade`

## Philosophy

**No Silent Failures**

- If a critical dependency is broken → service doesn't start
- If a migration fails → transaction rolls back, DB unchanged
- If semantic scoring unavailable → ERROR, not fallback

**Reproducibility**

- Poetry lock file → same dependencies everywhere
- Alembic migrations → same schema everywhere
- Version control → schema changes tracked in git

**Safety**

- Migrations are reversible
- Changes are reviewed before applying
- Production database can be rolled back

---

*Infrastructure improvements implemented: October 2025*
