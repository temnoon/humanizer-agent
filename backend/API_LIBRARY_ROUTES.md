# Library Routes API Documentation

## Overview

The Library API provides endpoints for browsing, searching, and managing imported collections (conversations), messages, chunks, media files, and transformation jobs. These routes support the hierarchical navigation of conversation archives imported from platforms like ChatGPT and Claude.

**Base Path**: `/api/library`

**Total Endpoints**: 11

---

## Table of Contents

1. [Collection Endpoints](#collection-endpoints)
   - [GET /collections](#1-get-apilibrarycollections)
   - [GET /collections/{collection_id}](#2-get-apilibrarycollectionscollection_id)
2. [Message Endpoints](#message-endpoints)
   - [GET /messages/{message_id}/chunks](#3-get-apilibrarymessagesmessage_idchunks)
3. [Search Endpoints](#search-endpoints)
   - [GET /search](#4-get-apilibrarysearch)
4. [Statistics Endpoints](#statistics-endpoints)
   - [GET /stats](#5-get-apilibrarystats)
5. [Media Endpoints](#media-endpoints)
   - [GET /media](#6-get-apilibrarymedia)
   - [GET /media/{media_id}/metadata](#7-get-apilibrarymediamedia_idmetadata)
   - [GET /media/{media_id}/file](#8-get-apilibrarymediamedia_idfile)
6. [Transformation Library Endpoints](#transformation-library-endpoints)
   - [GET /transformations](#9-get-apilibrarytransformations)
   - [GET /transformations/{job_id}](#10-get-apilibrarytransformationsjob_id)
   - [POST /transformations/{job_id}/reapply](#11-post-apilibrarytransformationsjob_idreapply)

---

## Collection Endpoints

### 1. GET /api/library/collections

**Purpose**: List all conversation collections with optional filtering and pagination.

**Parameters**:
- `source_platform` (query, optional): Filter by platform (e.g., 'chatgpt', 'claude')
- `collection_type` (query, optional): Filter by type (e.g., 'conversation', 'session')
- `search` (query, optional): Search term for title and description (case-insensitive)
- `limit` (query, optional): Maximum results (default: 50, max: 5000)
- `offset` (query, optional): Pagination offset (default: 0)

**Response Model**: `List[CollectionSummary]`

```python
class CollectionSummary(BaseModel):
    id: str
    title: str
    description: Optional[str]
    collection_type: str
    source_platform: Optional[str]
    message_count: int
    chunk_count: int
    media_count: int
    total_tokens: int
    word_count: int
    created_at: str
    original_date: Optional[str]  # Extracted from metadata.create_time or import_date
    import_date: Optional[str]
    metadata: dict
```

**Database Queries**:
- `SELECT FROM Collection` - Main query with ORDER BY created_at DESC
- Filters applied: `source_platform`, `collection_type`, title/description ILIKE search
- `SELECT SUM(array_length(string_to_array(content, ' '), 1)) FROM Chunk` - Word count calculation for each collection

**Side Effects**: None

**Error Cases**:
- None (returns empty list if no matches)

**Example Request**:
```http
GET /api/library/collections?source_platform=chatgpt&search=python&limit=10&offset=0
```

**Example Response**:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Python Programming Discussion",
    "description": "Conversation about advanced Python techniques",
    "collection_type": "conversation",
    "source_platform": "chatgpt",
    "message_count": 15,
    "chunk_count": 45,
    "media_count": 3,
    "total_tokens": 5000,
    "word_count": 3500,
    "created_at": "2025-10-01T12:00:00",
    "original_date": "2025-09-30T10:00:00",
    "import_date": "2025-10-01T12:00:00",
    "metadata": {"create_time": 1727694000}
  }
]
```

---

### 2. GET /api/library/collections/{collection_id}

**Purpose**: Get hierarchical view of a collection with its messages, optional chunk samples, and media files.

**Parameters**:
- `collection_id` (path, required): Collection UUID
- `include_chunks` (query, optional): Whether to include sample chunks (default: false)

**Response Model**: `CollectionHierarchy`

```python
class CollectionHierarchy(BaseModel):
    collection: CollectionSummary
    messages: List[MessageSummary]
    recent_chunks: List[ChunkDetail]  # Empty if include_chunks=false
    media: List[MediaDetail]
```

**Database Queries**:
- `SELECT FROM Collection WHERE id = collection_id` - Get collection
- `SELECT FROM Message WHERE collection_id = collection_id ORDER BY sequence_number` - Get all messages
- For each message: `SELECT FROM Chunk WHERE message_id = msg_id AND chunk_sequence = 0 LIMIT 1` - First chunk for preview
- If `include_chunks=true`: `SELECT FROM Chunk WHERE collection_id = collection_id ORDER BY created_at DESC LIMIT 10` - Sample chunks
- `SELECT FROM Media WHERE collection_id = collection_id` - All media files
- `SELECT SUM(array_length(string_to_array(content, ' '), 1)) FROM Chunk WHERE collection_id = collection_id` - Word count

**Side Effects**: None

**Error Cases**:
- 400: Invalid collection ID format (not a valid UUID)
- 404: Collection not found

**Example Request**:
```http
GET /api/library/collections/123e4567-e89b-12d3-a456-426614174000?include_chunks=true
```

**Example Response**:
```json
{
  "collection": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Python Programming Discussion",
    "description": "Conversation about advanced Python techniques",
    "collection_type": "conversation",
    "source_platform": "chatgpt",
    "message_count": 15,
    "chunk_count": 45,
    "media_count": 3,
    "total_tokens": 5000,
    "word_count": 3500,
    "created_at": "2025-10-01T12:00:00",
    "original_date": "2025-09-30T10:00:00",
    "import_date": "2025-10-01T12:00:00",
    "metadata": {}
  },
  "messages": [
    {
      "id": "msg-001",
      "collection_id": "123e4567-e89b-12d3-a456-426614174000",
      "sequence_number": 0,
      "role": "user",
      "message_type": "text",
      "summary": "Can you explain Python decorators?",
      "chunk_count": 3,
      "token_count": 150,
      "media_count": 0,
      "timestamp": "2025-09-30T10:00:00",
      "created_at": "2025-10-01T12:00:00",
      "metadata": {}
    }
  ],
  "recent_chunks": [
    {
      "id": "chunk-001",
      "message_id": "msg-001",
      "content": "Decorators in Python are...",
      "chunk_level": "message",
      "chunk_sequence": 0,
      "token_count": 50,
      "is_summary": false,
      "has_embedding": true,
      "created_at": "2025-10-01T12:00:00"
    }
  ],
  "media": [
    {
      "id": "file-abc123",
      "collection_id": "123e4567-e89b-12d3-a456-426614174000",
      "message_id": "msg-002",
      "media_type": "image",
      "mime_type": "image/png",
      "original_filename": "diagram.png",
      "size_bytes": 45000,
      "is_archived": true,
      "storage_path": "/path/to/media/file-abc123.png"
    }
  ]
}
```

---

## Message Endpoints

### 3. GET /api/library/messages/{message_id}/chunks

**Purpose**: Get all chunks for a specific message in sequence order.

**Parameters**:
- `message_id` (path, required): Message UUID

**Response Model**: `List[ChunkDetail]`

```python
class ChunkDetail(BaseModel):
    id: str
    message_id: str
    content: str
    chunk_level: str
    chunk_sequence: int
    token_count: Optional[int]
    is_summary: bool
    has_embedding: bool
    created_at: str
```

**Database Queries**:
- `SELECT FROM Message WHERE id = message_id` - Verify message exists
- `SELECT FROM Chunk WHERE message_id = message_id ORDER BY chunk_sequence` - Get all chunks

**Side Effects**: None

**Error Cases**:
- 400: Invalid message ID format (not a valid UUID)
- 404: Message not found

**Example Request**:
```http
GET /api/library/messages/msg-001/chunks
```

**Example Response**:
```json
[
  {
    "id": "chunk-001",
    "message_id": "msg-001",
    "content": "Can you explain Python decorators? I've seen them used in web frameworks but don't understand how they work.",
    "chunk_level": "message",
    "chunk_sequence": 0,
    "token_count": 25,
    "is_summary": false,
    "has_embedding": true,
    "created_at": "2025-10-01T12:00:00"
  }
]
```

---

## Search Endpoints

### 4. GET /api/library/search

**Purpose**: Search across collections, messages, and chunks using text matching.

**Parameters**:
- `query` (query, required): Search query string (minimum 2 characters)
- `search_type` (query, optional): What to search - 'all', 'collections', 'messages', or 'chunks' (default: 'all')
- `limit` (query, optional): Maximum results per type (default: 20, max: 1000)

**Response Model**: `dict`

```python
{
    "query": str,
    "collections": List[dict],
    "messages": List[dict],
    "chunks": List[dict]
}
```

**Database Queries**:
- If search_type = 'all' or 'collections': `SELECT FROM Collection WHERE title ILIKE '%query%' OR description ILIKE '%query%' LIMIT limit`
- If search_type = 'all' or 'chunks': `SELECT FROM Chunk WHERE content ILIKE '%query%' LIMIT limit`
- Messages search is not implemented (returns empty list)

**Side Effects**: None

**Error Cases**:
- 422: Query string too short (< 2 characters)
- 422: Invalid search_type (not one of: all, collections, messages, chunks)

**Example Request**:
```http
GET /api/library/search?query=python&search_type=all&limit=20
```

**Example Response**:
```json
{
  "query": "python",
  "collections": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Python Programming Discussion",
      "type": "conversation",
      "platform": "chatgpt"
    }
  ],
  "messages": [],
  "chunks": [
    {
      "id": "chunk-001",
      "message_id": "msg-001",
      "collection_id": "123e4567-e89b-12d3-a456-426614174000",
      "content_preview": "Can you explain Python decorators? I've seen them used in web frameworks but don't understand how they work..."
    }
  ]
}
```

---

## Statistics Endpoints

### 5. GET /api/library/stats

**Purpose**: Get overall library statistics including counts and platform breakdown.

**Parameters**: None

**Response Model**: `dict`

```python
{
    "collections": int,
    "messages": int,
    "chunks": int,
    "chunks_with_embeddings": int,
    "embedding_coverage": float,  # Percentage
    "media_files": int,
    "platforms": dict  # Platform name -> count
}
```

**Database Queries**:
- `SELECT COUNT(id) FROM Collection` - Total collections
- `SELECT COUNT(id) FROM Message` - Total messages
- `SELECT COUNT(id) FROM Chunk` - Total chunks
- `SELECT COUNT(id) FROM Chunk WHERE embedding IS NOT NULL` - Chunks with embeddings
- `SELECT COUNT(id) FROM Media` - Total media files
- `SELECT source_platform, COUNT(id) FROM Collection GROUP BY source_platform` - Platform breakdown

**Side Effects**: None

**Error Cases**: None

**Example Request**:
```http
GET /api/library/stats
```

**Example Response**:
```json
{
  "collections": 1660,
  "messages": 46379,
  "chunks": 33952,
  "chunks_with_embeddings": 33952,
  "embedding_coverage": 100.0,
  "media_files": 8640,
  "platforms": {
    "chatgpt": 1200,
    "claude": 460
  }
}
```

---

## Media Endpoints

### 6. GET /api/library/media

**Purpose**: List all media files with optional collection filtering and pagination.

**Parameters**:
- `collection_id` (query, optional): Filter by collection UUID
- `limit` (query, optional): Maximum results (default: 100, max: 10000)
- `offset` (query, optional): Pagination offset (default: 0)

**Response Model**: `dict`

```python
{
    "media": List[dict],
    "count": int
}
```

**Database Queries**:
- `SELECT FROM Media ORDER BY created_at DESC` - Main query
- Optional filter: `WHERE collection_id = collection_id`
- Pagination: `LIMIT limit OFFSET offset`

**Side Effects**:
- Deduplicates media records by `original_media_id` in-memory (handles database duplicates gracefully)

**Error Cases**: None

**Example Request**:
```http
GET /api/library/media?collection_id=123e4567-e89b-12d3-a456-426614174000&limit=50&offset=0
```

**Example Response**:
```json
{
  "media": [
    {
      "id": "file-abc123",
      "filename": "diagram.png",
      "mime_type": "image/png",
      "storage_path": "/path/to/media/file-abc123.png",
      "collection_id": "123e4567-e89b-12d3-a456-426614174000",
      "message_id": "msg-002",
      "created_at": "2025-10-01T12:00:00",
      "custom_metadata": {
        "width": 1024,
        "height": 768
      }
    }
  ],
  "count": 1
}
```

---

### 7. GET /api/library/media/{media_id}/metadata

**Purpose**: Get detailed metadata for a media file including conversation and message links.

**Parameters**:
- `media_id` (path, required): Original media ID (e.g., "file-BTGHeayl9isKTp9kvyBzirg0")

**Response Model**: `dict`

```python
{
    "id": str,
    "filename": Optional[str],
    "mime_type": Optional[str],
    "storage_path": Optional[str],
    "created_at": Optional[str],
    "custom_metadata": dict,
    "conversation": Optional[dict],  # Collection info
    "message": Optional[dict],       # Message info
    "transformations": List[dict]    # Currently empty, TODO
}
```

**Database Queries**:
- `SELECT FROM Media WHERE original_media_id = media_id` - Get media record
- `SELECT FROM Collection WHERE id = media.collection_id` - Get conversation info (if collection_id exists)
- `SELECT FROM Message WHERE id = media.message_id` - Get message info (if message_id exists)
- `SELECT content FROM Chunk WHERE message_id = message.id LIMIT 1` - Get message content preview

**Side Effects**: None

**Error Cases**:
- 404: Media not found

**Example Request**:
```http
GET /api/library/media/file-abc123/metadata
```

**Example Response**:
```json
{
  "id": "file-abc123",
  "filename": "diagram.png",
  "mime_type": "image/png",
  "storage_path": "/path/to/media/file-abc123.png",
  "created_at": "2025-10-01T12:00:00",
  "custom_metadata": {
    "width": 1024,
    "height": 768
  },
  "conversation": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Python Programming Discussion",
    "created_at": "2025-10-01T12:00:00",
    "source_platform": "chatgpt"
  },
  "message": {
    "id": "msg-002",
    "role": "assistant",
    "content": "Here's a diagram showing how decorators work...",
    "created_at": "2025-10-01T12:05:00"
  },
  "transformations": []
}
```

---

### 8. GET /api/library/media/{media_id}/file

**Purpose**: Serve the actual media file content for display or download.

**Parameters**:
- `media_id` (path, required): Original media ID (e.g., "file-BTGHeayl9isKTp9kvyBzirg0")

**Response Model**: Binary file response (FileResponse/Response)

**Database Queries**:
- `SELECT FROM Media WHERE original_media_id = media_id LIMIT 1` - Get media record (uses LIMIT 1 to handle duplicates)

**Side Effects**:
- Reads file from filesystem at `storage_path`
- Fallback filesystem search in `backend/media/chatgpt/` directory if not in database

**Error Cases**:
- 404 (with special detail): File is a placeholder (not found in archive)
  ```json
  {
    "error": "file_not_in_archive",
    "message": "Media file 'diagram.png' was referenced but not found in archive",
    "media_id": "file-abc123",
    "can_upload": true
  }
  ```
- 404: Media file not found anywhere

**Example Request**:
```http
GET /api/library/media/file-abc123/file
```

**Response Headers** (images):
```
Content-Type: image/png
Content-Disposition: inline
```

**Response Headers** (non-images):
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename*=UTF-8''diagram.png
```

**Notes**:
- Images are served with `Content-Disposition: inline` for browser display
- Non-images are served with `Content-Disposition: attachment` to trigger download
- Uses RFC 2231 encoding for Unicode filenames
- Supports ChatGPT file IDs (file-XXX format)

---

## Transformation Library Endpoints

### 9. GET /api/library/transformations

**Purpose**: List all transformation jobs with filtering and pagination. This is the "transformations library" - completed transformations that can be browsed and reapplied.

**Parameters**:
- `status` (query, optional): Filter by status ('completed', 'failed', 'pending', etc.)
- `job_type` (query, optional): Filter by job type ('persona_transform', 'madhyamaka_detect', etc.)
- `search` (query, optional): Search in job name and description (case-insensitive)
- `limit` (query, optional): Maximum results (default: 50, max: 200)
- `offset` (query, optional): Pagination offset (default: 0)

**Response Model**: `List[TransformationSummary]`

```python
class TransformationSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    job_type: str
    status: str
    created_at: str
    completed_at: Optional[str]
    total_items: int
    processed_items: int
    progress_percentage: float
    tokens_used: int
    configuration: dict
    source_message_id: Optional[str]      # Extracted from configuration
    source_collection_id: Optional[str]   # Extracted from configuration
```

**Database Queries**:
- `SELECT FROM TransformationJob ORDER BY created_at DESC` - Main query
- Filters applied: `status`, `job_type`, name/description ILIKE search
- Pagination: `LIMIT limit OFFSET offset`

**Side Effects**: None

**Error Cases**: None (returns empty list if no matches)

**Example Request**:
```http
GET /api/library/transformations?status=completed&job_type=persona_transform&limit=10
```

**Example Response**:
```json
[
  {
    "id": "job-001",
    "name": "Einstein Persona Transform",
    "description": "Transform message into Einstein's voice",
    "job_type": "persona_transform",
    "status": "completed",
    "created_at": "2025-10-05T14:00:00",
    "completed_at": "2025-10-05T14:02:30",
    "total_items": 5,
    "processed_items": 5,
    "progress_percentage": 100.0,
    "tokens_used": 2500,
    "configuration": {
      "persona": "Albert Einstein",
      "source_message_ids": ["msg-001"],
      "source_collection_id": "123e4567-e89b-12d3-a456-426614174000"
    },
    "source_message_id": "msg-001",
    "source_collection_id": "123e4567-e89b-12d3-a456-426614174000"
  }
]
```

---

### 10. GET /api/library/transformations/{job_id}

**Purpose**: Get detailed view of a transformation job including source content, results, and lineage information.

**Parameters**:
- `job_id` (path, required): Transformation job UUID

**Response Model**: `TransformationDetail`

```python
class TransformationDetail(BaseModel):
    job: TransformationSummary
    source_message: Optional[MessageSummary]
    source_collection: Optional[CollectionSummary]
    transformations: List[dict]  # ChunkTransformation details
    lineage: List[dict]          # Lineage information
```

**Database Queries**:
- `SELECT FROM TransformationJob WHERE id = job_id` - Get job
- If source_message_id in config: `SELECT FROM Message WHERE id = source_message_id` - Get source message
- For source message: `SELECT FROM Chunk WHERE message_id = msg_id AND chunk_sequence = 0 LIMIT 1` - First chunk for preview
- If source_collection_id in config: `SELECT FROM Collection WHERE id = source_collection_id` - Get source collection
- `SELECT SUM(array_length(string_to_array(content, ' '), 1)) FROM Chunk WHERE collection_id = col_id` - Word count for collection
- `SELECT FROM ChunkTransformation WHERE job_id = job_id ORDER BY sequence_number` - All chunk transformations
- `SELECT FROM TransformationLineage WHERE job_id IN job_ids ORDER BY generation` - Lineage records (uses PostgreSQL ARRAY.any())

**Side Effects**: None

**Error Cases**:
- 400: Invalid job ID format (not a valid UUID)
- 404: Transformation job not found

**Example Request**:
```http
GET /api/library/transformations/job-001
```

**Example Response**:
```json
{
  "job": {
    "id": "job-001",
    "name": "Einstein Persona Transform",
    "description": "Transform message into Einstein's voice",
    "job_type": "persona_transform",
    "status": "completed",
    "created_at": "2025-10-05T14:00:00",
    "completed_at": "2025-10-05T14:02:30",
    "total_items": 5,
    "processed_items": 5,
    "progress_percentage": 100.0,
    "tokens_used": 2500,
    "configuration": {
      "persona": "Albert Einstein",
      "source_message_ids": ["msg-001"]
    },
    "source_message_id": "msg-001",
    "source_collection_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "source_message": {
    "id": "msg-001",
    "collection_id": "123e4567-e89b-12d3-a456-426614174000",
    "sequence_number": 0,
    "role": "user",
    "message_type": "text",
    "summary": "Can you explain Python decorators?",
    "chunk_count": 3,
    "token_count": 150,
    "media_count": 0,
    "timestamp": "2025-09-30T10:00:00",
    "created_at": "2025-10-01T12:00:00",
    "metadata": {}
  },
  "source_collection": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Python Programming Discussion",
    "description": null,
    "collection_type": "conversation",
    "source_platform": "chatgpt",
    "message_count": 15,
    "chunk_count": 45,
    "media_count": 3,
    "total_tokens": 5000,
    "word_count": 3500,
    "created_at": "2025-10-01T12:00:00",
    "original_date": "2025-09-30T10:00:00",
    "import_date": "2025-10-01T12:00:00",
    "metadata": {}
  },
  "transformations": [
    {
      "id": "trans-001",
      "job_id": "job-001",
      "source_chunk_id": "chunk-001",
      "transformed_chunk_id": "chunk-101",
      "sequence_number": 0,
      "status": "completed",
      "created_at": "2025-10-05T14:01:00"
    }
  ],
  "lineage": [
    {
      "id": "lineage-001",
      "source_chunk_id": "chunk-001",
      "derived_chunk_id": "chunk-101",
      "job_ids": ["job-001"],
      "generation": 1,
      "transformation_type": "persona_transform"
    }
  ]
}
```

---

### 11. POST /api/library/transformations/{job_id}/reapply

**Purpose**: Reapply a completed transformation to new content by creating a new transformation job with the same configuration.

**Parameters**:
- `job_id` (path, required): Source transformation job UUID
- `target_message_id` (query, required): Message ID to apply transformation to

**Request Body**: None

**Response Model**: `dict`

```python
{
    "job_id": str,        # New job UUID
    "status": str,        # "pending"
    "message": str        # Status message
}
```

**Database Queries**:
- `SELECT FROM TransformationJob WHERE id = job_id` - Get source job
- `SELECT FROM Message WHERE id = target_message_id` - Verify target message exists
- `SELECT id FROM Chunk WHERE message_id = target_message_id` - Get chunks for target message
- `INSERT INTO TransformationJob` - Create new job
- Commit transaction and refresh

**Side Effects**:
- Creates a new TransformationJob record with status "pending"
- Job will be picked up by background processor
- New job inherits configuration from source job but targets new content

**Error Cases**:
- 400: Invalid UUID format (job_id or target_message_id)
- 404: Source transformation job not found
- 404: Target message not found
- 400: Target message has no chunks

**Example Request**:
```http
POST /api/library/transformations/job-001/reapply?target_message_id=msg-002
```

**Example Response**:
```json
{
  "job_id": "job-002",
  "status": "pending",
  "message": "Transformation queued for processing"
}
```

**Notes**:
- New job name is "{original_name} (reapplied)"
- New job description is "Reapplied from job {job_id}"
- Configuration is copied from source job but updated with new target references:
  - `source_message_ids` → [target_message_id]
  - `source_chunk_ids` → chunk IDs from target message
  - `source_collection_id` → target message's collection_id
- Extra metadata stores original job reference:
  ```json
  {
    "reapplied_from": "job-001",
    "original_job_name": "Einstein Persona Transform"
  }
  ```

---

## Data Models Reference

### Collections
- **Collection** (table): Top-level conversation/archive container
- Fields: id, title, description, collection_type, source_platform, message_count, chunk_count, media_count, total_tokens, created_at, import_date, extra_metadata

### Messages
- **Message** (table): Individual message/turn in a conversation
- Fields: id, collection_id, sequence_number, role, message_type, chunk_count, token_count, media_count, timestamp, created_at, extra_metadata

### Chunks
- **Chunk** (table): Text segments with embeddings for semantic search
- Fields: id, message_id, collection_id, content, chunk_level, chunk_sequence, token_count, is_summary, embedding, created_at

### Media
- **Media** (table): Images, files, attachments referenced in conversations
- Fields: id, collection_id, message_id, original_media_id, media_type, mime_type, original_filename, size_bytes, is_archived, storage_path, created_at, extra_metadata
- **Note**: Database may contain duplicate records with same original_media_id; API deduplicates in-memory

### Transformations
- **TransformationJob** (table): Transformation job metadata
- Fields: id, user_id, session_id, name, description, job_type, status, total_items, processed_items, progress_percentage, tokens_used, configuration, priority, created_at, completed_at, extra_metadata

- **ChunkTransformation** (table): Individual chunk transformation results
- Fields: id, job_id, source_chunk_id, transformed_chunk_id, sequence_number, status, created_at

- **TransformationLineage** (table): Provenance tracking for transformations
- Fields: id, source_chunk_id, derived_chunk_id, job_ids (array), generation, transformation_type, created_at

---

## Common Patterns

### Pagination
Most list endpoints support pagination via `limit` and `offset` parameters:
- Default limits vary by endpoint (20-100)
- Maximum limits are configurable (200-10000)
- Frontend can adjust limits via dropdown

### Filtering
Common filter parameters:
- `source_platform`: Filter by platform (chatgpt, claude)
- `collection_type`: Filter by type (conversation, session)
- `status`: Filter transformations by status
- `job_type`: Filter transformations by type

### Search
Text search uses PostgreSQL ILIKE for case-insensitive matching:
- Wraps query in `%...%` for substring matching
- Applies to title, description, content fields
- Minimum 2 characters required

### Error Handling
Standard HTTP status codes:
- 200: Success
- 400: Invalid request (bad UUID format, validation errors)
- 404: Resource not found
- 422: Validation error (Pydantic validation, invalid enum values)

### UUID Handling
All ID parameters are validated as UUIDs:
```python
try:
    uuid_obj = UUID(id_string)
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid UUID format")
```

### Date Handling
Dates are returned as ISO 8601 strings:
- `created_at`: Database record creation time
- `original_date`: Original conversation creation time (extracted from metadata.create_time Unix timestamp)
- `import_date`: When conversation was imported
- `timestamp`: Message/event timestamp

### Metadata Extraction
Collection original dates are extracted from `extra_metadata.create_time`:
```python
if 'create_time' in metadata and metadata['create_time']:
    from datetime import datetime
    original_date = datetime.fromtimestamp(metadata['create_time']).isoformat()
```

### Content Truncation
Long content is truncated for previews:
- Message summaries: First 200 chars
- Chunk content in hierarchy views: 500 chars
- Search result previews: 200 chars

---

## Performance Considerations

### Word Count Calculation
Word counts are calculated on-demand using PostgreSQL:
```sql
SELECT SUM(array_length(string_to_array(content, ' '), 1))
FROM Chunk WHERE collection_id = ?
```
This runs for each collection in list views - may be slow for large result sets. Consider caching or pre-computation.

### Chunk Preview Queries
Collection hierarchy endpoint runs one query per message to get first chunk (N+1 pattern). For collections with many messages, this could be optimized with a JOIN or batch query.

### Media Deduplication
Media deduplication happens in-memory after database query. For large media lists, this could be optimized with a DISTINCT ON query or database-level deduplication.

### Transformation Lineage
Lineage queries use PostgreSQL ARRAY.any() which may not use indexes efficiently. For large lineage graphs, consider denormalization or indexing strategies.

---

## Integration Notes

### Frontend Integration
These endpoints support the following frontend features:
- **LibraryBrowser**: Collection/message browsing with pagination and search
- **ImageBrowser**: Media file browsing with infinite scroll
- **TransformationsLibrary**: Transformation job browsing and reapplication
- **ConversationViewer**: Message and chunk display with media embedding
- **ImageGallery**: Inline media display in conversations

### Background Processing
Transformation jobs created via `/transformations/{job_id}/reapply` are queued with status "pending" and processed by a separate background worker (not part of this API).

### File Serving
Media files are served directly via `/media/{media_id}/file` with appropriate Content-Type and Content-Disposition headers for browser display or download.

### Archive Import
Collections, messages, chunks, and media are created by archive import processes (ChatGPT/Claude conversation exports). These endpoints provide read-only access to imported data.

---

## Future Enhancements (TODOs in Code)

1. **Media Transformation Linkage** (line 693-695):
   - Track which transformations reference specific media files
   - Return in `/media/{media_id}/metadata` endpoint

2. **Message Search** (line 436-502):
   - Search endpoint currently doesn't search Message table
   - Could add message role/type filtering

3. **Database Deduplication** (line 591-598):
   - Remove duplicate media records at database level
   - Add unique constraint on `original_media_id`

4. **Word Count Caching** (line 192-197):
   - Pre-compute and cache word counts in Collection table
   - Avoid expensive calculation on every list request

5. **Chunk Preview Optimization** (line 260-273):
   - Use JOIN or batch query to get first chunks for all messages
   - Avoid N+1 query pattern

---

## Security Considerations

### Input Validation
- All UUIDs validated before database queries
- Search queries sanitized via SQLAlchemy parameterization (ILIKE with % wrapping)
- Query parameters use Pydantic validation (min_length, regex, le constraints)

### File Serving
- Media files served from controlled storage_path only
- Fallback filesystem search limited to `backend/media/chatgpt/` directory
- Unicode filename handling via RFC 2231 encoding
- MIME type detection prevents serving arbitrary file types

### SQL Injection
- All queries use SQLAlchemy ORM or parameterized queries
- No raw SQL string interpolation

### Access Control
- No authentication/authorization implemented (TODO)
- All data is currently accessible without restrictions
- Future: Add user_id filtering, role-based access

---

## Dependencies

### Python Packages
- `fastapi`: Web framework
- `sqlalchemy`: ORM and async database
- `pydantic`: Data validation and serialization
- `uuid`: UUID validation
- `pathlib`: File path handling
- `mimetypes`: MIME type detection

### Database
- PostgreSQL with pgvector extension
- Async session via `sqlalchemy.ext.asyncio`

### Models
- `models.chunk_models`: Collection, Message, Chunk, Media
- `models.pipeline_models`: TransformationJob, ChunkTransformation, TransformationLineage

---

## Testing Recommendations

### Unit Tests
1. Response model validation (Pydantic schemas)
2. UUID parsing and error handling
3. Search pattern construction
4. Date/metadata extraction logic
5. Content truncation logic

### Integration Tests
1. Collection listing with various filters
2. Hierarchy retrieval with include_chunks flag
3. Search across different types
4. Media metadata with linked conversation/message
5. Transformation reapplication workflow
6. Pagination edge cases (offset beyond results, limit=0)

### E2E Tests
1. Full collection browsing flow
2. Media file serving and display
3. Transformation library browsing and filtering
4. Search and navigation to results
5. Reapply transformation to new content

### Performance Tests
1. Large collection listing (1000+ collections)
2. Collection with many messages (100+ messages)
3. Search with high result counts
4. Media list with pagination (10000 records)
5. Word count calculation overhead

### Error Case Tests
1. Invalid UUID formats (400 errors)
2. Non-existent resources (404 errors)
3. Missing media files (404 with special detail)
4. Search query too short (422 error)
5. Reapply to message with no chunks (400 error)

---

## Changelog

- **Oct 2025**: Initial documentation created
- Bug fixes: Media duplicate handling (line 591-598), Unicode filename encoding (line 758-760)
- Features: Deduplication, word count calculation, transformation reapplication

---

**End of Documentation**
