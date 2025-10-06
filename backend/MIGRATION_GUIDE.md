# Infrastructure Migration Guide

## Overview

This guide covers migrating from pip/requirements.txt to Poetry and from manual table creation to Alembic migrations.

## Why This Matters

### Poetry vs pip
- **Lock files**: `poetry.lock` ensures identical dependencies across environments
- **Dependency resolution**: Poetry prevents version conflicts (like the `sentence-transformers` + `huggingface_hub` issue)
- **Dev dependencies**: Separate test/lint tools from production dependencies
- **Reproducible builds**: No more "works on my machine"

### Alembic vs create_all()
- **Version control**: Every schema change is tracked in git
- **Rollback capability**: Can revert breaking migrations
- **Team collaboration**: No more schema drift between developers
- **Production safety**: Migrations are tested before deployment

## Migration Steps

### 1. Install Poetry (if not already installed)

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or via homebrew
brew install poetry
```

### 2. Remove Old Virtual Environment

```bash
cd /Users/tem/humanizer-agent/backend

# Deactivate if currently active
deactivate 2>/dev/null || true

# Remove old venv
rm -rf venv/
```

### 3. Install Dependencies with Poetry

```bash
# Install all dependencies (production + dev)
poetry install

# Activate the new virtual environment
poetry shell

# Verify critical dependencies
python -c "import sentence_transformers; print('✓ sentence-transformers OK')"
python -c "import asyncpg; print('✓ asyncpg OK')"
python -c "import alembic; print('✓ alembic OK')"
```

### 4. Create Initial Alembic Migration

**IMPORTANT**: Only run this if you're starting fresh OR if you want to create baseline migration for existing DB.

#### Option A: Fresh Database (Recommended)

```bash
cd /Users/tem/humanizer-agent/backend

# Drop existing database (WARNING: destroys all data)
psql -U humanizer -d postgres -c "DROP DATABASE IF EXISTS humanizer;"
psql -U humanizer -d postgres -c "CREATE DATABASE humanizer;"

# Enable pgvector extension
psql -U humanizer -d humanizer -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create initial migration (auto-generate from models)
alembic revision --autogenerate -m "Initial schema with all tables"

# Apply migration
alembic upgrade head
```

#### Option B: Existing Database (Create Baseline)

```bash
cd /Users/tem/humanizer-agent/backend

# Mark current schema as baseline (don't apply changes)
alembic revision --autogenerate -m "Baseline from existing schema"

# Mark as applied without running (assumes DB already has these tables)
alembic stamp head
```

### 5. Update Startup Script

The application now validates dependencies at startup. If `sentence-transformers` is broken, **the service will NOT start**.

No more silent fallbacks. No more degraded mode.

### 6. Verify Everything Works

```bash
# Start backend (should validate dependencies first)
cd /Users/tem/humanizer-agent/backend
poetry run python main.py

# You should see:
# ======================================================================
# VALIDATING CRITICAL DEPENDENCIES
# ======================================================================
# ✓ sentence-transformers: OK
# ✓ asyncpg (PostgreSQL driver): OK
# ✓ pgvector: OK
# ✓ anthropic: OK
# ======================================================================
# ALL CRITICAL DEPENDENCIES VALIDATED ✓
# ======================================================================
```

## Daily Workflow Changes

### Running the Application

```bash
# Old way (deprecated)
cd backend && source venv/bin/activate && python main.py

# New way
cd backend && poetry run python main.py

# Or activate Poetry shell once
cd backend && poetry shell
python main.py
```

### Adding Dependencies

```bash
# Add production dependency
poetry add fastapi

# Add dev dependency
poetry add --group dev pytest

# Update lock file after manual pyproject.toml edits
poetry lock

# Install updated dependencies
poetry install
```

### Database Migrations

```bash
# Create migration after model changes
alembic revision --autogenerate -m "Add new column to users table"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Check current migration status
alembic current

# View migration history
alembic history
```

## Updating Start Script

Update `/Users/tem/humanizer-agent/start.sh`:

```bash
#!/bin/bash

# Start backend with Poetry
cd backend
poetry run python main.py &
BACKEND_PID=$!

# Start frontend (unchanged)
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
```

## Troubleshooting

### Poetry install fails

```bash
# Clear cache
poetry cache clear pypi --all

# Try install again
poetry install
```

### Dependency conflicts

```bash
# Update all dependencies to latest compatible versions
poetry update

# Check for outdated packages
poetry show --outdated
```

### Alembic can't autogenerate

Check that:
1. All model files are imported in `alembic/env.py`
2. Models inherit from `Base`
3. Database connection string in `alembic.ini` is correct

### Migration fails

```bash
# Check what would be applied
alembic upgrade head --sql

# View current status
alembic current

# Force stamp to specific revision (dangerous!)
alembic stamp <revision_id>
```

## What Changed

### Files Created
- `backend/pyproject.toml` - Poetry configuration
- `backend/poetry.lock` - Locked dependencies (auto-generated)
- `backend/core_dependencies.py` - Fail-fast validation
- `backend/alembic.ini` - Alembic configuration
- `backend/alembic/env.py` - Migration environment
- `backend/alembic/versions/*.py` - Migration scripts

### Files Modified
- `backend/main.py` - Added `validate_dependencies()` call at startup

### Files Deprecated (can delete after migration)
- `backend/requirements.txt` - Replaced by `pyproject.toml`
- `backend/venv/` - Replaced by Poetry-managed virtualenv

## Benefits

1. **Broken dependencies = startup failure** (no silent degradation)
2. **Reproducible environments** (poetry.lock ensures identical installs)
3. **Schema versioning** (every DB change tracked in git)
4. **Safe rollbacks** (can revert migrations in production)
5. **Better collaboration** (team members get exact same environment)

## Next Steps

After verifying everything works:
1. Delete `backend/requirements.txt`
2. Delete `backend/venv/`
3. Update documentation to reference Poetry commands
4. Add `poetry.lock` to git (important!)
5. Update CI/CD to use `poetry install` instead of `pip install`
