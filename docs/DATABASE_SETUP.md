# Database Setup Guide

This guide covers setting up PostgreSQL with pgvector for the Humanizer Agent.

## Overview

The Humanizer Agent uses PostgreSQL with the pgvector extension for:
- **User and session management**: Track users and organize transformations into sessions
- **Vector embeddings**: Enable semantic search across transformations
- **Belief pattern tracking**: Identify recurring frameworks and philosophical tendencies

## Prerequisites

### 1. Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@17
brew services start postgresql@17
```

> **Note:** PostgreSQL 17, 16, and 15 are all supported. The setup script will auto-detect your version.

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Fedora/RHEL:**
```bash
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
```

### 2. Install pgvector Extension

**macOS (Homebrew):**
```bash
brew install pgvector
```

> **Note:** pgvector works with PostgreSQL 17, 16, 15, and earlier versions.

**Ubuntu/Debian:**
```bash
# For PostgreSQL 17
sudo apt-get install postgresql-17-pgvector

# For PostgreSQL 15
sudo apt-get install postgresql-15-pgvector
```

**From source (all platforms):**
```bash
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

## Quick Setup

Run the automated setup script:

```bash
cd backend
chmod +x setup_db.sh
./setup_db.sh
```

This will:
1. Create the `humanizer` database
2. Create the `humanizer` user (password: `humanizer`)
3. Install the pgvector extension
4. Run all schema migrations

## Manual Setup

If you prefer manual setup or need custom configuration:

### 1. Create Database and User

```bash
psql postgres
```

```sql
-- Create user
CREATE USER humanizer WITH PASSWORD 'humanizer';

-- Create database
CREATE DATABASE humanizer OWNER humanizer;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE humanizer TO humanizer;

-- Exit
\q
```

### 2. Enable pgvector Extension

```bash
psql -d humanizer
```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### 3. Run Schema Migration

```bash
psql -d humanizer -U humanizer -f database/schema.sql
```

## Configuration

Update your `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set:

```
DATABASE_URL=postgresql+asyncpg://humanizer:humanizer@localhost:5432/humanizer
```

## Database Schema

### Tables

**users**
- Stores user accounts (supports anonymous users)
- Fields: id, email, username, is_anonymous, preferences

**sessions**
- Groups related transformations
- Fields: id, user_id, title, description, transformation_count, is_archived

**transformations**
- Individual transformation records with embeddings
- Fields: id, session_id, source_text, source_embedding (vector), persona, namespace, style, transformed_content, transformed_embedding (vector)

**belief_patterns**
- Tracks recurring belief frameworks
- Fields: id, user_id, pattern_name, pattern_embedding (vector), frequency_count

### Vector Indexes

The schema includes HNSW indexes for fast vector similarity search:

```sql
CREATE INDEX idx_transformations_source_embedding ON transformations
    USING hnsw (source_embedding vector_cosine_ops);
```

## Verification

Test the database connection:

```bash
psql -d humanizer -U humanizer -c "SELECT version();"
psql -d humanizer -U humanizer -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

## Embedding Configuration

The system supports multiple embedding providers. Update `.env`:

```
# For Voyage AI (recommended)
EMBEDDING_MODEL=voyage-3
EMBEDDING_DIMENSION=1536

# For OpenAI
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

**Note:** The current implementation uses mock embeddings for development. To use real embeddings, update `backend/database/embeddings.py` with your preferred provider (Voyage AI, OpenAI, or Cohere).

## Vector Search Examples

### Find Similar Transformations

```sql
-- Find transformations similar to a given embedding
SELECT
    id,
    source_text,
    1 - (source_embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM transformations
WHERE source_embedding IS NOT NULL
ORDER BY source_embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### Using Helper Functions

The schema includes helper functions:

```sql
-- Find similar transformations (threshold 0.8, max 10 results)
SELECT * FROM find_similar_transformations(
    '[0.1, 0.2, ...]'::vector(1536),
    0.8,
    10
);

-- Get session summary with stats
SELECT * FROM get_session_summary('session-uuid-here');
```

## Backup and Restore

### Backup

```bash
pg_dump -U humanizer humanizer > humanizer_backup.sql
```

### Restore

```bash
psql -U humanizer humanizer < humanizer_backup.sql
```

## Troubleshooting

### Connection Errors

If you get connection errors:

1. Check PostgreSQL is running:
   ```bash
   pg_isready
   ```

2. Verify authentication in `pg_hba.conf`:
   ```bash
   # Find pg_hba.conf location
   psql postgres -c "SHOW hba_file;"

   # Add this line for local development
   host    humanizer    humanizer    127.0.0.1/32    md5
   ```

3. Reload PostgreSQL:
   ```bash
   # macOS
   brew services restart postgresql@15

   # Linux
   sudo systemctl restart postgresql
   ```

### pgvector Not Found

If pgvector extension fails to install:

1. Verify PostgreSQL version (15+ recommended, 17 fully supported)
2. Install pgvector from source (see Prerequisites)
3. Restart PostgreSQL after installation:
   ```bash
   # macOS
   brew services restart postgresql@17

   # Linux
   sudo systemctl restart postgresql
   ```

### Migration Errors

If schema migration fails:

1. Check for existing tables:
   ```sql
   \dt
   ```

2. Drop and recreate (⚠️ destroys data):
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   GRANT ALL ON SCHEMA public TO humanizer;
   ```

3. Re-run migration:
   ```bash
   psql -d humanizer -U humanizer -f database/schema.sql
   ```

## Production Deployment

For production environments:

1. **Use strong passwords**: Update the `humanizer` user password
2. **Enable SSL**: Configure PostgreSQL to require SSL connections
3. **Set connection pooling**: Use PgBouncer or similar
4. **Configure backups**: Set up automated daily backups
5. **Monitor performance**: Use pg_stat_statements extension

Example production DATABASE_URL:
```
DATABASE_URL=postgresql+asyncpg://humanizer:strong_password@db.example.com:5432/humanizer?ssl=require
```

## Migration from SQLite

If migrating from the old SQLite database:

1. Keep old database as backup
2. Export session data if needed
3. Update DATABASE_URL in `.env`
4. Restart backend server
5. Test session creation and transformation

The new schema is backwards-compatible with session concepts but adds vector search capabilities.
