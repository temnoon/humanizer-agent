# Session Management & PostgreSQL Integration

## Overview

The Humanizer Agent now includes comprehensive session management built on PostgreSQL with pgvector for semantic search capabilities.

## New Features

### 1. Session Organization
- Group related transformations into sessions
- Auto-create sessions or manually organize your work
- Track session history and statistics
- Archive old sessions

### 2. Persistent History
- All transformations saved to PostgreSQL
- Load previous work and continue transformations
- Clone sessions to explore variations
- Delete unwanted sessions

### 3. Vector Search (Foundation)
- Database schema includes pgvector embeddings
- Ready for semantic similarity search
- Find related transformations by meaning (coming soon)
- Belief pattern tracking infrastructure

### 4. User Management
- Supports anonymous users (no registration required)
- User ID stored in browser localStorage
- Option for authenticated users in future

## Quick Setup

### 1. Install PostgreSQL + pgvector

**macOS:**
```bash
brew install postgresql@17 pgvector
brew services start postgresql@17
```

> **Note:** The setup script supports PostgreSQL 17, 16, and 15. It will auto-detect your version.

**Ubuntu:**
```bash
sudo apt-get install postgresql postgresql-contrib postgresql-17-pgvector
sudo systemctl start postgresql
```

### 2. Run Database Setup

```bash
cd backend
chmod +x setup_db.sh
./setup_db.sh
```

This creates:
- Database: `humanizer`
- User: `humanizer` (password: `humanizer`)
- Tables: users, sessions, transformations, belief_patterns
- Indexes: HNSW vector indexes for fast similarity search

### 3. Update Configuration

Edit `backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://humanizer:humanizer@localhost:5432/humanizer
```

### 4. Install Dependencies

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

New dependencies:
- `asyncpg` - PostgreSQL async driver
- `pgvector` - Vector extension support
- `psycopg2-binary` - PostgreSQL adapter
- `numpy` - Vector calculations

### 5. Start Application

```bash
./start.sh
```

## Using Session Management

### Create a Session

1. Open the application (http://localhost:5173)
2. Click the sidebar toggle button (left edge)
3. Click **"+ New Session"**
4. Enter a session title
5. Start transforming text

Sessions auto-save all transformations.

### Navigate Sessions

**Sidebar Features:**
- View all sessions (most recent first)
- Click any session to load it
- See transformation count and last updated time
- Filter archived sessions

**Session Actions:**
- **Clone**: Create a copy to explore variations
- **Archive**: Hide from main view (keeps data)
- **Delete**: Permanently remove (⚠️ cannot be undone)

### Continue Previous Work

1. Open sidebar
2. Click on a session
3. Most recent transformation loads automatically
4. Continue with new transformations or modify parameters

### Session Statistics

Each session tracks:
- Total transformations
- Unique personas used
- Unique namespaces explored
- Unique styles applied
- Total tokens consumed
- Date range of work

Access via: `GET /api/sessions/{id}/stats`

## API Endpoints

### Session Management

**Create Session:**
```bash
POST /api/sessions
{
  "title": "Quantum Philosophy Explorations",
  "description": "Exploring quantum concepts through different belief frameworks",
  "user_id": "optional-user-uuid"
}
```

**List Sessions:**
```bash
GET /api/sessions?user_id={uuid}&include_archived=false&limit=50
```

**Get Session Details:**
```bash
GET /api/sessions/{session_id}
```

Returns session with all transformations.

**Update Session:**
```bash
PATCH /api/sessions/{session_id}
{
  "title": "New Title",
  "is_archived": true
}
```

**Clone Session:**
```bash
POST /api/sessions/{session_id}/clone?new_title=Session (Copy)
```

**Delete Session:**
```bash
DELETE /api/sessions/{session_id}
```

**Get Session Transformations:**
```bash
GET /api/sessions/{session_id}/transformations
```

**Get Session Statistics:**
```bash
GET /api/sessions/{session_id}/stats
```

### User Management

**Create Anonymous User:**
```bash
POST /api/sessions/users
{
  "is_anonymous": true
}
```

**Get User:**
```bash
GET /api/sessions/users/{user_id}
```

## Database Schema

### Tables

**users**
- `id` (UUID, primary key)
- `email` (nullable for anonymous users)
- `username` (nullable)
- `is_anonymous` (boolean, default true)
- `created_at`, `updated_at`
- `preferences` (JSONB)

**sessions**
- `id` (UUID, primary key)
- `user_id` (foreign key to users)
- `title` (varchar 500)
- `description` (text)
- `transformation_count` (integer, auto-incremented)
- `is_archived` (boolean)
- `created_at`, `updated_at`
- `metadata` (JSONB)

**transformations**
- `id` (UUID, primary key)
- `session_id`, `user_id` (foreign keys)
- `source_text`, `source_embedding` (vector 1536)
- `persona`, `namespace`, `style`
- `transformed_content`, `transformed_embedding` (vector 1536)
- `belief_framework` (JSONB)
- `emotional_profile`, `philosophical_context`
- `status`, `error_message`
- `tokens_used`, `processing_time_ms`
- `created_at`, `completed_at`
- `parent_transformation_id` (self-reference)
- `is_checkpoint` (boolean)
- `metadata` (JSONB)

**belief_patterns**
- `id` (UUID, primary key)
- `user_id` (foreign key)
- `pattern_name`
- `persona`, `namespace`, `style`
- `frequency_count`, `first_seen`, `last_seen`
- `pattern_embedding` (vector 1536)
- `philosophical_insight`, `emotional_signature`
- `metadata` (JSONB)

### Vector Indexes

HNSW indexes for fast approximate nearest neighbor search:

```sql
CREATE INDEX idx_transformations_source_embedding ON transformations
    USING hnsw (source_embedding vector_cosine_ops);

CREATE INDEX idx_transformations_transformed_embedding ON transformations
    USING hnsw (transformed_embedding vector_cosine_ops);

CREATE INDEX idx_belief_patterns_embedding ON belief_patterns
    USING hnsw (pattern_embedding vector_cosine_ops);
```

### Helper Functions

**Find Similar Transformations:**
```sql
SELECT * FROM find_similar_transformations(
    query_embedding::vector(1536),
    similarity_threshold := 0.8,
    max_results := 10
);
```

**Get Session Summary:**
```sql
SELECT * FROM get_session_summary('session-uuid');
```

Returns aggregated statistics including unique frameworks, token usage, and date range.

## Frontend Integration

### SessionSidebar Component

**Props:**
- `currentSessionId` - Active session UUID
- `onSessionSelect` - Callback when session selected
- `onNewSession` - Callback when new session created
- `isVisible` - Sidebar visibility state
- `onToggleVisibility` - Toggle sidebar

**Usage:**
```jsx
<SessionSidebar
  currentSessionId={currentSession?.id}
  onSessionSelect={handleSessionSelect}
  onNewSession={handleNewSession}
  isVisible={sidebarVisible}
  onToggleVisibility={() => setSidebarVisible(!sidebarVisible)}
/>
```

### State Management

**localStorage Keys:**
- `humanizer_user_id` - Anonymous user UUID
- `current_session_id` - Active session UUID

**Session Loading:**
```javascript
// Load session on mount
useEffect(() => {
  const savedSessionId = localStorage.getItem('current_session_id')
  if (savedSessionId) {
    axios.get(`/api/sessions/${savedSessionId}`)
      .then(response => setCurrentSession(response.data))
  }
}, [])
```

## Vector Search (Coming Soon)

The database is ready for semantic search. To enable:

### 1. Configure Embedding Provider

Edit `backend/.env`:
```
EMBEDDING_MODEL=voyage-3
EMBEDDING_DIMENSION=1536
ENABLE_VECTOR_SEARCH=true
```

### 2. Choose Provider

Update `backend/database/embeddings.py`:

**Voyage AI (Recommended):**
```python
import voyageai
vo = voyageai.Client(api_key="...")
result = vo.embed([text], model="voyage-3")
return result.embeddings[0]
```

**OpenAI:**
```python
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key="...")
response = await client.embeddings.create(
    input=text,
    model="text-embedding-3-small"
)
return response.data[0].embedding
```

### 3. Search Similar Transformations

Once embeddings are enabled:

```python
# API endpoint (coming soon)
GET /api/sessions/{session_id}/similar?limit=10

# Returns sessions with similar content based on vector similarity
```

## Belief Pattern Tracking (Coming Soon)

The system will automatically track:
- Recurring persona/namespace/style combinations
- Frequency of each pattern
- Emotional signatures
- Philosophical insights

Access via:
```bash
GET /api/philosophical/patterns?user_id={uuid}
```

## Database Maintenance

### Backup
```bash
pg_dump -U humanizer humanizer > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
psql -U humanizer humanizer < backup_20250104.sql
```

### Vacuum (optimize)
```bash
psql -U humanizer -d humanizer -c "VACUUM ANALYZE;"
```

### Check Size
```bash
psql -U humanizer -d humanizer -c "
SELECT
    pg_size_pretty(pg_database_size('humanizer')) as database_size,
    pg_size_pretty(pg_total_relation_size('transformations')) as transformations_size;
"
```

## Troubleshooting

### "relation does not exist"
- Run database setup script: `./backend/setup_db.sh`
- Or manually: `psql -U humanizer -d humanizer -f backend/database/schema.sql`

### "pgvector extension not found"
- Install pgvector: `brew install pgvector` (macOS) or from source
- Enable: `psql -U humanizer -d humanizer -c "CREATE EXTENSION vector;"`

### "connection refused"
- Check PostgreSQL is running: `pg_isready`
- Start: `brew services start postgresql@17` (macOS) or `sudo systemctl start postgresql` (Linux)

### Sessions not loading
- Check backend logs for database errors
- Verify DATABASE_URL in `.env`
- Test connection: `psql $DATABASE_URL -c "SELECT 1;"`

### Slow queries
- Ensure indexes are created (check schema.sql)
- Run VACUUM ANALYZE
- Check query performance: Enable `echo=True` in `backend/database/connection.py`

## Migration from SQLite

The old SQLite database (`humanizer.db`) is no longer used. To migrate:

1. Export old sessions (if any)
2. Update DATABASE_URL to PostgreSQL
3. Restart backend
4. Create new sessions

The new schema provides:
- Better concurrency
- Vector search capabilities
- Advanced querying
- Production scalability

## Production Recommendations

### Security
1. Change `humanizer` user password:
   ```sql
   ALTER USER humanizer WITH PASSWORD 'strong_random_password';
   ```
2. Update DATABASE_URL with new password
3. Enable SSL: `DATABASE_URL=postgresql+asyncpg://...?ssl=require`

### Performance
1. Use connection pooling (PgBouncer)
2. Configure proper indexes
3. Regular VACUUM ANALYZE
4. Monitor with pg_stat_statements

### Backup
1. Automated daily backups
2. Off-site storage
3. Test restore procedures
4. Point-in-time recovery setup

### Monitoring
1. Track database size
2. Monitor query performance
3. Set up alerts for errors
4. Log slow queries

## Future Enhancements

### Planned Features
- [ ] Vector similarity search UI
- [ ] Belief pattern visualization
- [ ] Session analytics dashboard
- [ ] Collaborative sessions (multi-user)
- [ ] Export session to PDF/Markdown
- [ ] Session templates
- [ ] Auto-tagging with ML
- [ ] Semantic search across all sessions

### Database Optimizations
- [ ] Partitioning for large datasets
- [ ] Materialized views for analytics
- [ ] Read replicas for scaling
- [ ] Time-series data for patterns

## Support

For database-specific questions, see:
- [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) - Detailed setup guide
- [backend/database/schema.sql](backend/database/schema.sql) - Full schema
- PostgreSQL documentation: https://www.postgresql.org/docs/
- pgvector documentation: https://github.com/pgvector/pgvector

---

**Session management enables witnessing your belief structures evolve through time.**
