# Chunk-Based Database Architecture

## Overview

The Humanizer Agent uses a **chunk-based database architecture** that stores all content (AI conversations, transformations, social media, documents) as hierarchical text chunks with progressive summarization and vector embeddings.

This architecture enables:
- ✅ Fine-grain semantic search (find specific ideas, not just whole documents)
- ✅ Multi-level embeddings (document, paragraph, sentence)
- ✅ Progressive summarization (base chunks → section summaries → message summary)
- ✅ Flexible content types (conversations, transformations, contemplations, social media)
- ✅ Media integration (images, audio, video with OCR/transcription)
- ✅ Relationship graphs (transformations, citations, replies)

---

## Core Concepts

### 1. Collections

**Collections** are top-level containers that group related content.

**Types:**
- `conversation`: AI chat (ChatGPT, Claude)
- `session`: Transformation session (Humanizer multi-perspective)
- `document`: Document collection
- `archive`: Social media archive (Twitter, Facebook)
- `custom`: User-defined

**Attributes:**
- `title`, `description`
- `source_platform` (chatgpt, claude, humanizer, twitter, facebook)
- `source_format` (chatgpt_json, claude_project, twitter_api)
- `original_id` (platform-specific ID for traceability)
- Statistics: `message_count`, `chunk_count`, `media_count`, `total_tokens`

**Example:**
```json
{
  "id": "coll_123",
  "title": "Quantum Consciousness Discussion",
  "collection_type": "conversation",
  "source_platform": "chatgpt",
  "original_id": "chatgpt_conv_abc123",
  "message_count": 42,
  "chunk_count": 523,
  "total_tokens": 15780
}
```

---

### 2. Messages

**Messages** are individual messages within collections.

**Roles:**
- `system`: System prompts
- `user`: User messages
- `assistant`: AI responses
- `tool`: Tool calls/results

**Key Features:**
- Ordered by `sequence_number` within collection
- Supports nesting (`parent_message_id` for tool calls inside assistant messages)
- Each message has ONE summary chunk (`summary_chunk_id`)
- Flexible `metadata` for belief frameworks, tool calls, etc.

**Example:**
```json
{
  "id": "msg_456",
  "collection_id": "coll_123",
  "sequence_number": 5,
  "role": "assistant",
  "summary_chunk_id": "chunk_summary_xyz",
  "chunk_count": 12,
  "token_count": 384,
  "metadata": {
    "tool_calls": [
      {"name": "web_search", "arguments": {"query": "quantum entanglement"}}
    ]
  }
}
```

---

### 3. Chunks

**Chunks** are text at any granularity level with hierarchical structure.

**Hierarchy:**
```
Message (e.g., 10,000 tokens)
  └── Message Summary Chunk (1 chunk summarizing entire message)
       └── Section Summary Chunks (summarize groups of consecutive chunks)
            └── Base Chunks (sentences/paragraphs, ~320 tokens each)
```

**Chunk Levels:**
- `document`: Whole message (rare)
- `paragraph`: Paragraph-level chunks (~320 tokens typical)
- `sentence`: Sentence-level chunks (for important/novel ideas)

**Summarization Types:**
- Base chunks: `is_summary=false`
- Section summaries: `is_summary=true`, `summary_type='section_summary'`
- Message summaries: `is_summary=true`, `summary_type='message_summary'`

**Key Features:**
- Vector embedding for semantic search (`embedding` field)
- Parent/child relationships (`parent_chunk_id`)
- Position tracking (`char_start`, `char_end` for exact reconstruction)
- Flexible `metadata` for all use cases

**Example Base Chunk:**
```json
{
  "id": "chunk_abc",
  "message_id": "msg_456",
  "content": "Quantum entanglement suggests that particles remain connected across vast distances...",
  "chunk_level": "paragraph",
  "chunk_sequence": 3,
  "token_count": 287,
  "embedding": [0.123, -0.456, ...],  // 1024-dim vector
  "embedding_model": "mxbai-embed-large",
  "is_summary": false,
  "char_start": 450,
  "char_end": 1870
}
```

**Example Summary Chunk:**
```json
{
  "id": "chunk_summary_xyz",
  "message_id": "msg_456",
  "content": "This message discusses quantum entanglement, consciousness, and the observer effect in physics.",
  "chunk_level": "document",
  "chunk_sequence": 0,
  "token_count": 23,
  "is_summary": true,
  "summary_type": "message_summary",
  "summarizes_chunk_ids": ["chunk_sec1", "chunk_sec2", "chunk_sec3"]
}
```

---

### 4. Chunk Relationships

**Chunk Relationships** track non-linear connections between chunks.

**Relationship Types:**
- `transforms_into`: Transformation (source → transformed)
- `cites`: Citation/quote
- `responds_to`: Conversational reply
- `continues`: Continuation/split
- `summarizes`: Summary relationship
- `contradicts`: Philosophical opposition
- `supports`: Philosophical agreement
- `references`: General reference
- `derived_from`: Derived content (OCR, transcription)

**Example:**
```json
{
  "source_chunk_id": "chunk_original",
  "target_chunk_id": "chunk_transformed",
  "relationship_type": "transforms_into",
  "strength": 1.0,
  "metadata": {
    "belief_framework": {
      "persona": "Scholar",
      "namespace": "quantum-physics",
      "style": "formal"
    }
  }
}
```

---

### 5. Media

**Media** stores images, audio, video, documents with OCR/transcription.

**Key Features:**
- Linked to collection and message
- Archival support: remove `blob_data`, keep `metadata` + `embedding`
- OCR from images → chunks (`generated_chunk_ids`)
- Transcription from audio → chunks
- Vector embeddings for images (CLIP) and audio

**Example:**
```json
{
  "id": "media_789",
  "collection_id": "coll_123",
  "message_id": "msg_456",
  "media_type": "image",
  "mime_type": "image/png",
  "original_filename": "quantum_diagram.png",
  "is_archived": false,
  "blob_data": "<binary data>",
  "embedding": [0.234, -0.567, ...],  // CLIP embedding
  "extracted_text": "Figure 1: Quantum Entanglement...",
  "extraction_method": "ocr_claude",
  "extraction_confidence": 0.95,
  "generated_chunk_ids": ["chunk_ocr_1", "chunk_ocr_2"]
}
```

**Archival:**
When archived, `blob_data` is removed but metadata preserved:
```json
{
  "is_archived": true,
  "blob_data": null,
  "storage_path": "/archive/media_789.png",
  "archive_metadata": {
    "archived_at": "2025-10-05T12:00:00Z",
    "reason": "user_request",
    "original_hash": "sha256:abc123...",
    "original_size_bytes": 1048576
  }
}
```

---

### 6. Belief Frameworks

**Belief Frameworks** track persona/namespace/style combinations.

**Purpose:**
- Track which frameworks are used most
- Find similar frameworks via embeddings
- Recommend frameworks based on usage

**Example:**
```json
{
  "id": "framework_123",
  "persona": "Scholar",
  "namespace": "quantum-physics",
  "style": "formal",
  "usage_count": 42,
  "framework_definition": {
    "core_values": ["precision", "wonder"],
    "communication_style": {"formality": 0.8, "creativity": 0.6}
  },
  "representative_embedding": [0.345, -0.678, ...]  // Centroid of all uses
}
```

---

## Progressive Summarization

### Algorithm

```
1. Import message (e.g., 10,000 tokens)
   ↓
2. Semantic chunking → Base chunks (~320 tokens each)
   - Store as chunks with chunk_level='paragraph' or 'sentence'
   - Generate embeddings for each
   ↓
3. Group consecutive chunks (context-dependent grouping)
   - Groups of 3-5 chunks (adjust based on semantic coherence)
   ↓
4. Generate section summaries
   - LLM summarizes each group → summary chunk
   - Store with is_summary=true, summary_type='section_summary'
   - summarizes_chunk_ids = [chunk1, chunk2, chunk3, ...]
   ↓
5. Generate message summary
   - LLM summarizes all section summaries → one message summary chunk
   - Store with is_summary=true, summary_type='message_summary'
   - Update messages.summary_chunk_id
   ↓
6. Link to message
   - All chunks reference message_id
   - Message has summary_chunk_id
```

### Example Hierarchy

```
Message ID: msg_456 (10,000 tokens, 42 chunks)
├── Summary Chunk: chunk_msg_summary
│   └── "This message discusses quantum entanglement, consciousness..."
│
├── Section Summary 1: chunk_sec1
│   └── "Introduction to quantum mechanics and observer effect..."
│   ├── Base Chunk 1: "Quantum mechanics is the branch of physics..."
│   ├── Base Chunk 2: "The observer effect suggests that measurement..."
│   └── Base Chunk 3: "In the famous double-slit experiment..."
│
├── Section Summary 2: chunk_sec2
│   └── "Deep dive into entanglement and non-locality..."
│   ├── Base Chunk 4: "Entanglement is a phenomenon where..."
│   └── Base Chunk 5: "Einstein called this 'spooky action'..."
│
└── Section Summary 3: chunk_sec3
    └── "Implications for consciousness and philosophy..."
    ├── Base Chunk 6: "Some philosophers argue that..."
    └── Base Chunk 7: "This connects to the hard problem..."
```

---

## Retrieval Strategies

### 1. Get Message Summary Only

**Use Case:** Display conversation history compactly

**SQL:**
```sql
SELECT c.*
FROM messages m
JOIN chunks c ON c.id = m.summary_chunk_id
WHERE m.collection_id = 'coll_123'
ORDER BY m.sequence_number;
```

**Result:** One summary chunk per message

---

### 2. Get Full Message with All Chunks

**Use Case:** Display full message with hierarchy

**SQL:**
```sql
SELECT * FROM get_message_chunk_hierarchy('msg_456');
```

**Result:** All chunks in hierarchical order (summary → sections → base)

---

### 3. Semantic Search Across All Chunks

**Use Case:** Find specific ideas, not just whole documents

**SQL:**
```sql
SELECT * FROM find_similar_chunks(
  query_embedding := '[0.123, -0.456, ...]'::vector(1024),
  similarity_threshold := 0.7,
  max_results := 20,
  filter_user_id := 'user_123',
  filter_chunk_level := 'paragraph'
);
```

**Result:** Ranked chunks with similarity scores

---

### 4. Get Related Chunks via Relationships

**Use Case:** Find transformations, citations, replies

**SQL:**
```sql
SELECT * FROM get_related_chunks(
  chunk_uuid := 'chunk_abc',
  relationship_types := ARRAY['transforms_into', 'cites'],
  max_depth := 2
);
```

**Result:** Related chunks via relationship graph

---

## Breadcrumb Navigation

Every chunk result includes full context:

```json
{
  "chunk_id": "chunk_abc",
  "content": "Quantum entanglement suggests...",
  "similarity": 0.87,
  "breadcrumbs": {
    "collection": {
      "id": "coll_123",
      "title": "Quantum Consciousness Discussion",
      "source_platform": "chatgpt"
    },
    "message": {
      "id": "msg_456",
      "role": "assistant",
      "sequence_number": 5,
      "timestamp": "2023-10-01T12:00:00Z"
    },
    "parent_chunks": [
      {"id": "chunk_sec1", "level": "section_summary"},
      {"id": "chunk_msg_summary", "level": "message_summary"}
    ],
    "media": [
      {"id": "media_789", "type": "image", "filename": "quantum_diagram.png"}
    ]
  }
}
```

This allows:
- Jump from chunk → full message
- See which collection/conversation it's from
- View associated media
- Navigate up/down the hierarchy

---

## Use Cases

### ChatGPT Conversation Import

```python
collection = Collection(
    title="Quantum Consciousness Discussion",
    collection_type="conversation",
    source_platform="chatgpt",
    original_id="chatgpt_conv_abc123"
)

for chatgpt_message in chatgpt_json['mapping'].values():
    message = Message(
        collection=collection,
        role=chatgpt_message['role'],
        sequence_number=seq
    )

    # Chunk message content
    base_chunks = semantic_chunk(chatgpt_message['content'])
    for chunk in base_chunks:
        chunk.message = message

    # Summarization
    section_summaries = create_section_summaries(base_chunks)
    message_summary = create_message_summary(section_summaries)
    message.summary_chunk_id = message_summary.id

    # OCR from images
    for attachment in chatgpt_message['attachments']:
        media = Media(
            collection=collection,
            message=message,
            media_type='image',
            blob_data=download_image(attachment)
        )
        ocr_chunks = ocr_image(media)
        media.generated_chunk_ids = [c.id for c in ocr_chunks]
```

---

### Multi-Perspective Transformation

```python
# Source message
source_message = Message(
    collection=session,
    role="user",
    message_type="transformation"
)
source_chunk = Chunk(
    message=source_message,
    content="Success requires dedication and hard work."
)

# Transform into 3 perspectives
for persona, namespace in [("Scholar", "academic"), ("Poet", "aesthetic"), ("Skeptic", "philosophy")]:
    transformed_message = Message(
        collection=session,
        role="assistant",
        message_type="transformation",
        metadata={"persona": persona, "namespace": namespace}
    )

    transformed_chunk = Chunk(
        message=transformed_message,
        content=transform(source_chunk.content, persona, namespace)
    )

    # Link via relationship
    ChunkRelationship(
        source_chunk=source_chunk,
        target_chunk=transformed_chunk,
        relationship_type="transforms_into",
        metadata={"belief_framework": {"persona": persona, "namespace": namespace}}
    )
```

---

### Contemplative Exercise Storage

```python
# User selects text from old conversation
source_chunk = get_chunk("chunk_from_old_conv")

# Generate word dissolution exercise
exercise_message = Message(
    collection=session,
    role="assistant",
    message_type="contemplation",
    metadata={
        "exercise_type": "word_dissolution",
        "target_word": "success",
        "source_chunk_id": source_chunk.id
    }
)

# Exercise content as chunks
dissolution_chunk = Chunk(
    message=exercise_message,
    content="Dissolution guidance: Feel the weight of 'success'...",
    metadata={"exercise_stage": "guidance"}
)

# Link to source
ChunkRelationship(
    source_chunk=source_chunk,
    target_chunk=dissolution_chunk,
    relationship_type="responds_to"
)

# User's response (if they answer the contemplation)
user_response_message = Message(
    collection=session,
    role="user",
    parent_message_id=exercise_message.id
)
```

---

## Embedding Strategy

### Embedding Models

**Local (Recommended):**
- **mxbai-embed-large** (1024 dims) - Best quality for local
- **nomic-embed-text** (768 dims) - Good quality, smaller

**Remote:**
- **OpenAI ada-002** (1536 dims) - Highest quality, costs money

### When to Embed

Generate embeddings for:
- ✅ All base chunks (paragraph, sentence)
- ✅ All section summaries
- ✅ All message summaries
- ✅ OCR text from images
- ✅ Transcriptions from audio
- ✅ Images (using CLIP)

**Don't embed:**
- ❌ Very short chunks (<10 tokens)
- ❌ Duplicate content

### Embedding Pipeline

```python
async def generate_embeddings_for_chunk(chunk: Chunk):
    # Use Ollama mxbai-embed-large
    embedding = await ollama_embed(
        model="mxbai-embed-large",
        text=chunk.content
    )

    chunk.embedding = embedding
    chunk.embedding_model = "mxbai-embed-large"
    chunk.embedding_generated_at = datetime.now()
```

---

## Database Setup

### 1. Install PostgreSQL + pgvector

```bash
# macOS
brew install postgresql@15
brew install pgvector

# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb humanizer
```

### 2. Initialize Schema

```bash
cd backend/database
python init_chunk_db.py --database-url postgresql://localhost/humanizer
```

### 3. Verify

```bash
psql humanizer -c "\dt"  # List tables
psql humanizer -c "SELECT * FROM collections LIMIT 1;"
```

---

## Migration from Old Schema

### Phase 1: Parallel Deployment

- Keep old schema (`sessions`, `transformations`)
- Deploy new schema (`collections`, `messages`, `chunks`)
- Dual-write: save to both schemas temporarily

### Phase 2: Backfill

```python
async def migrate_old_to_new():
    # Migrate sessions → collections
    for session in old_sessions:
        collection = Collection(
            title=session.title,
            collection_type="session",
            source_platform="humanizer"
        )

        # Migrate transformations → messages + chunks
        for transformation in session.transformations:
            # Source message
            source_msg = Message(
                collection=collection,
                role="user",
                sequence_number=i*2
            )
            source_chunk = Chunk(
                message=source_msg,
                content=transformation.source_text,
                embedding=transformation.source_embedding
            )

            # Transformed message
            transformed_msg = Message(
                collection=collection,
                role="assistant",
                sequence_number=i*2+1,
                metadata={
                    "persona": transformation.persona,
                    "namespace": transformation.namespace
                }
            )
            transformed_chunk = Chunk(
                message=transformed_msg,
                content=transformation.transformed_content,
                embedding=transformation.transformed_embedding
            )
```

### Phase 3: Cutover

- Update all APIs to use new schema
- Deprecate old tables
- Remove dual-write logic

---

## Performance Considerations

### Indexing

All critical indexes are created automatically:
- Vector indexes (HNSW) for semantic search
- B-tree indexes for foreign keys
- GIN indexes for JSONB metadata
- Full-text indexes for content search

### Query Optimization

**DO:**
- ✅ Filter by `user_id`, `collection_id` first
- ✅ Use `chunk_level` filter for semantic search
- ✅ Limit results with `LIMIT`
- ✅ Use views (`message_summaries`) for common queries

**DON'T:**
- ❌ Scan all chunks without filters
- ❌ Request embeddings unless needed
- ❌ Load full hierarchies for list views

### Embedding Generation

- Generate embeddings asynchronously
- Batch process imports (50-100 chunks at a time)
- Use local Ollama for free embeddings
- Cache embeddings (never regenerate unless content changes)

---

## API Examples

See `backend/api/chunk_routes.py` for full API implementation.

**Key Endpoints:**
- `GET /api/collections` - List collections
- `GET /api/collections/{id}` - Get collection with stats
- `GET /api/collections/{id}/messages` - Get messages (summaries only)
- `GET /api/messages/{id}/full` - Get full message with all chunks
- `POST /api/chunks/search` - Semantic search
- `POST /api/collections/import/chatgpt` - Import ChatGPT conversations.json
- `POST /api/media/{id}/archive` - Archive media (remove blob)

---

## Conclusion

The chunk-based architecture provides:
- **Flexibility**: Store any content type (conversations, transformations, social media)
- **Granularity**: Search at any level (document, paragraph, sentence)
- **Scalability**: Progressive summarization reduces search space
- **Context**: Breadcrumb navigation maintains full context
- **Efficiency**: Archive media to reduce storage costs

**Next Steps:**
1. Initialize database: `python init_chunk_db.py`
2. Setup embedding model: `ollama pull mxbai-embed-large`
3. Import ChatGPT data: `python chatgpt_importer.py`
4. Test semantic search: `python search_service.py`
