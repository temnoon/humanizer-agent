# Embedding Generation Guide

## Overview

This guide covers the embedding generation system for the Humanizer Agent. The system intelligently generates vector embeddings for text chunks, with smart filtering to skip low-value content.

## Tools

### 1. dbexplore - Database Exploration

**Purpose:** Explore and debug the database, analyze content patterns.

**Usage:**
```bash
cd backend

# Overall statistics
./dbexplore stats

# Chunk analysis (by level, content type, token distribution)
./dbexplore chunks

# Embedding statistics (coverage, models used)
./dbexplore embeddings

# Find low-interest content (slash commands, "continue", zero tokens)
./dbexplore low-interest

# Sample random chunks
./dbexplore sample 20

# Custom SQL query
./dbexplore query "SELECT COUNT(*) FROM chunks WHERE token_count > 1000"
```

**Example Output:**
```
Chunks to Embed: 125,799 (90% of database)
- 15-50 tokens: 26,955
- 101-500 tokens: 49,526 (largest group)
- Total: ~50 million tokens

Chunks to Skip: 13,433 (10%)
- 9,612 too short (<15 tokens)
- 3,060 slash commands
- 724 low-interest words
- 37 zero tokens
```

### 2. embedgen - Embedding Generation Pipeline

**Purpose:** Generate embeddings for high-value chunks with intelligent filtering.

**Workflow:**

```bash
# 1. Plan what will be embedded (dry run)
./embedgen plan --min-tokens 15

# 2. Mark chunks for embedding
./embedgen queue --min-tokens 15

# 3. Generate embeddings (requires Ollama)
./embedgen process --batch-size 100

# 4. Check progress
./embedgen status

# 5. Reset queue if needed
./embedgen reset
```

## Filtering Logic

The system automatically filters out low-value content:

### What Gets Embedded (High-Value Content)

- ✅ Token count >= 15 (configurable minimum)
- ✅ Substantive content (conversations, documents, analysis)
- ✅ No existing embeddings

### What Gets Skipped (Low-Interest Content)

- ❌ Zero token chunks
- ❌ Chunks below minimum token threshold
- ❌ Slash commands (content starts with `/`)
- ❌ Low-interest single words:
  - `continue`, `go on`, `keep going`, `next`, `more`
  - `ok`, `yes`, `no`, `k`, `kk`, `yep`, `nope`
- ❌ Chunks that already have embeddings

## Database Statistics

**Current State (Oct 7, 2025):**
- Total chunks: 139,232
- With embeddings: 0
- Need embeddings: 125,799 (after filtering)
- Low-interest chunks: 13,433 (auto-skipped)

**Token Distribution:**
- Range: 1 to 25,671 tokens
- Average: 360 tokens
- Total to process: ~50 million tokens

## Embedding Model

**Model:** mxbai-embed-large (Ollama)
- **Dimension:** 1024
- **Context:** 8192 tokens max
- **Speed:** ~50 chunks/second (local)

**Requirements:**
```bash
# Start Ollama
ollama serve

# Pull model (first time only, ~700MB)
ollama pull mxbai-embed-large
```

**Alternative:** nomic-embed-text (768 dimensions, 274MB)
- Smaller, faster, but requires database schema change
- Database currently configured for 1024 dimensions

## Configuration

**Default Settings:**
- Minimum tokens: 15
- Batch size: 100 chunks
- Ollama URL: http://localhost:11434

**Adjustable:**
```bash
# Lower minimum (more inclusive)
./embedgen plan --min-tokens 10

# Higher minimum (more selective)
./embedgen plan --min-tokens 25

# Larger batches (faster, more memory)
./embedgen process --batch-size 200
```

## Performance Estimates

**Local Ollama (mxbai-embed-large):**
- Speed: ~50 chunks/second
- 125,799 chunks ÷ 50/sec = ~42 minutes
- Memory: ~2GB RAM

**Batch Processing:**
- Recommended: 100-200 chunks/batch
- Saves progress after each batch
- Resumable (re-run `./embedgen process` to continue)

## Monitoring Progress

**Check Status:**
```bash
./embedgen status
```

**Output:**
```
Overall Progress:
  Total chunks: 139,232
  With embeddings: 45,000 (32%)
  Without embeddings: 94,232

Queue Status:
  Queued: 80,799
  Processed: 45,000

Recent Embeddings (Last 10):
  [Shows recently embedded chunks with timestamps]
```

## Common Tasks

### Initial Setup

```bash
# 1. Check database state
./dbexplore stats
./dbexplore chunks

# 2. Analyze what will be embedded
./dbexplore low-interest
./embedgen plan --min-tokens 15

# 3. Start embedding generation
./embedgen queue --min-tokens 15
./embedgen process
```

### Resume After Interruption

```bash
# Check current progress
./embedgen status

# Continue processing
./embedgen process
```

### Change Minimum Token Threshold

```bash
# Reset queue
./embedgen reset

# Plan with new threshold
./embedgen plan --min-tokens 25

# Queue with new filter
./embedgen queue --min-tokens 25

# Process
./embedgen process
```

### Analyze Embedding Coverage

```bash
# Overall stats
./dbexplore embeddings

# Check which chunks still need embeddings
./dbexplore query "
SELECT
    chunk_level,
    COUNT(*) as without_embeddings
FROM chunks
WHERE embedding IS NULL
GROUP BY chunk_level
ORDER BY without_embeddings DESC;
"
```

## Database Schema

**Chunks Table:**
```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    token_count INTEGER,

    -- Embedding fields
    embedding vector(1024),
    embedding_model TEXT,
    embedding_generated_at TIMESTAMP WITH TIME ZONE,

    -- Metadata (JSONB)
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_chunks_embedding
ON chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m=16, ef_construction=64);

CREATE INDEX idx_chunks_embedding_model
ON chunks (embedding_model);
```

**Queue Metadata:**
```json
{
  "embedding_queued": true,
  "embedding_queued_at": "2025-10-07T14:30:00",
  "embedding_filter": "min_tokens=15"
}
```

## Semantic Search

Once embeddings are generated, you can perform semantic search:

```python
from sqlalchemy import select, text
from models.chunk_models import Chunk

# Find similar chunks
query_embedding = await embedding_service.generate_embedding("your search text")

stmt = select(Chunk).where(
    Chunk.embedding.is_not(None)
).order_by(
    Chunk.embedding.cosine_distance(query_embedding)
).limit(10)

results = await session.execute(stmt)
similar_chunks = results.scalars().all()
```

## Troubleshooting

### Ollama Not Running

**Error:** `❌ Error: Ollama is not running`

**Solution:**
```bash
ollama serve
```

### Model Not Installed

**Error:** `model 'mxbai-embed-large' not found`

**Solution:**
```bash
ollama pull mxbai-embed-large
```

### Out of Memory

**Error:** Process killed or system freezes

**Solution:**
```bash
# Reduce batch size
./embedgen process --batch-size 50

# Or use smaller model
ollama pull nomic-embed-text  # 274MB vs 700MB
```

### Slow Performance

**Issue:** Embeddings generating too slowly

**Solutions:**
1. Increase batch size: `--batch-size 200`
2. Use GPU-accelerated Ollama (if available)
3. Use cloud API (OpenAI, Voyage) instead of Ollama

### Database Connection Errors

**Issue:** Can't connect to database

**Solution:**
```bash
# Check active profile
./dbswitch current

# Switch to production
./dbswitch switch production

# Verify connection
./dbexplore stats
```

## Advanced Usage

### Custom Filtering

Edit `embedgen` script to add custom filters:

```bash
# Add to FILTER_SQL variable
FILTER_SQL="
    ...existing filters...

    -- Custom: Skip chunks with specific keywords
    AND content NOT LIKE '%[REDACTED]%'

    -- Custom: Only embed chunks from specific collection
    AND collection_id = 'your-collection-uuid'
"
```

### Batch Export for Cloud Processing

```bash
# Export chunks to JSON for cloud embedding services
./dbexplore query "
SELECT
    id,
    content,
    token_count
FROM chunks
WHERE
    token_count >= 15
    AND embedding IS NULL
" -o chunks_to_embed.json
```

### Monitor with PostgreSQL

```sql
-- Real-time embedding progress
SELECT
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) * 100.0 / COUNT(*) as pct_complete,
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as embedded,
    COUNT(*) as total
FROM chunks;

-- Embedding generation rate (chunks/minute)
SELECT
    DATE_TRUNC('minute', embedding_generated_at) as minute,
    COUNT(*) as chunks_per_minute
FROM chunks
WHERE embedding_generated_at > NOW() - INTERVAL '1 hour'
GROUP BY minute
ORDER BY minute DESC;
```

## Best Practices

1. **Always run `plan` before `queue`**
   - Verify filtering logic matches expectations
   - Check token distribution
   - Estimate processing time

2. **Start with higher minimum token threshold**
   - Use 15-20 tokens minimum
   - Very short chunks often lack context
   - Can lower threshold later if needed

3. **Monitor queue status during processing**
   - Check `./embedgen status` periodically
   - Look for failed embeddings
   - Verify model is consistent

4. **Backup before large operations**
   - Use `./dbinit backup humanizer`
   - Embeddings are expensive to regenerate

5. **Use appropriate batch sizes**
   - Smaller (50-100): Lower memory, slower
   - Larger (200-500): Higher memory, faster
   - Adjust based on system resources

## Next Steps

After embeddings are generated:

1. **Semantic Search**: Find similar chunks by meaning
2. **Clustering**: Group related content
3. **Transformation Discovery**: Find transformation patterns
4. **Belief Framework Analysis**: Identify persona/namespace/style patterns
5. **Contemplation Exercise Generation**: Generate philosophical exercises

## Support

For issues or questions:
- Check `./dbexplore low-interest` for filtering issues
- Review `./embedgen status` for processing errors
- Check PostgreSQL logs for database errors
- Verify Ollama is running: `curl http://localhost:11434/api/version`

---

**Last Updated:** October 7, 2025
**Version:** 1.0
**Tools:** dbexplore, embedgen
**Model:** mxbai-embed-large (1024 dim)
