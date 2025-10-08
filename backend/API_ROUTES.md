# Transformation API Routes Documentation

**File**: `/Users/tem/humanizer-agent/backend/api/routes.py`
**Lines**: 567
**Endpoints**: 10
**Router Prefix**: `/api`
**Tags**: `transformations`

---

## Overview

This module provides the core transformation API endpoints for the Humanizer Agent. It handles narrative transformation operations using PERSONA, NAMESPACE, and STYLE parameters to transform text content through the Claude Agent SDK. The API supports both single-pass and chunked transformations, checkpoint/rollback functionality, token validation, and transformation history tracking.

**Key Features**:
- Narrative transformation with configurable parameters
- Token limit validation with tier-based limits (free/premium)
- Automatic chunking for long documents (premium tier)
- Checkpoint and rollback functionality
- Background task processing with progress tracking
- Dual storage system (PostgreSQL + legacy storage)
- Content analysis for extracting inherent characteristics

---

## API Endpoints

### 1. Test Endpoint

**HTTP Method & Path**: `GET /api/test`

**Purpose**: Health check endpoint to verify that the transformation agent and storage systems are operational.

**Parameters**: None

**Response Model**: JSON object (no Pydantic schema)

**Database Queries**:
- Creates test transformation in storage
- Deletes test transformation after verification
- No PostgreSQL queries

**Side Effects**:
- Creates temporary transformation in storage system
- Tests agent client initialization
- Cleans up test data

**Error Cases**: Returns error object with traceback if any system fails

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/test
```

**Example Response**:
```json
{
  "storage": "ok",
  "agent": {
    "model": "claude-3-5-sonnet-20241022",
    "has_client": true
  },
  "message": "All systems operational"
}
```

**Error Response**:
```json
{
  "error": "Connection refused",
  "traceback": "Traceback (most recent call last):\n..."
}
```

---

### 2. Check Document Tokens

**HTTP Method & Path**: `POST /api/check-tokens`

**Purpose**: Validates whether a document is within token limits for the user's subscription tier. Returns token count, word estimate, and whether chunking is needed.

**Parameters**:
- **Body** (JSON):
  - `content` (string, required): Text content to check
  - `user_tier` (string, optional): User subscription tier - "free" or "premium" (default: "free")

**Response Model**: JSON object (no Pydantic schema)

**Database Queries**: None

**Side Effects**: None (read-only operation)

**Error Cases**:
- `500 Internal Server Error`: Token check failed

**Token Limits**:
- **Free tier input**: 30,000 tokens
- **Free tier output**: 10,000 tokens
- **Premium tier input**: 150,000 tokens (with auto-chunking)
- **Premium tier output**: 50,000 tokens

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/check-tokens \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your text content here...",
    "user_tier": "free"
  }'
```

**Example Response**:
```json
{
  "token_count": 25000,
  "word_estimate": 18750,
  "token_limit": 30000,
  "is_within_limit": true,
  "message": "Within token limit",
  "needs_chunking": false,
  "num_chunks": 1,
  "tier": "free"
}
```

**Chunking Example (Premium tier)**:
```json
{
  "token_count": 120000,
  "word_estimate": 90000,
  "token_limit": 150000,
  "is_within_limit": true,
  "message": "Within token limit",
  "needs_chunking": true,
  "num_chunks": 3,
  "tier": "premium"
}
```

**Error Response**:
```json
{
  "detail": "Token check failed: Invalid content"
}
```

---

### 3. Create Transformation

**HTTP Method & Path**: `POST /api/transform`

**Purpose**: Initiates a new narrative transformation. The transformation runs in the background and can be monitored via the status endpoint. Supports both single-pass and chunked transformations based on content length and user tier.

**Parameters**:
- **Body** (`TransformationRequest`):
  - `content` (string, required): Text content to transform
  - `persona` (string, required): Target persona/voice (e.g., "academic researcher", "tech blogger")
  - `namespace` (string, required): Conceptual framework/domain (e.g., "philosophy", "software engineering")
  - `style` (TransformationStyle enum, required): Writing style - one of:
    - `formal`, `casual`, `academic`, `creative`, `technical`, `journalistic`
  - `preserve_structure` (boolean, optional): Maintain original structure (default: `true`)
  - `depth` (float, optional): Transformation depth from 0.0 (minimal) to 1.0 (deep) (default: `0.5`)
  - `user_tier` (string, optional): User subscription tier - "free" or "premium" (default: "free")
  - `session_id` (string, optional): Session ID to associate transformation with
  - `user_id` (string, optional): User ID for the transformation

**Response Model**: `TransformationResponse`
- `id` (string): Unique transformation job ID (UUID)
- `status` (TransformationStatusEnum): Always "pending" on creation
- `created_at` (datetime): Creation timestamp
- `message` (string): Success message with chunking info if applicable

**Database Queries**:
1. **TransformationStorage** (legacy system):
   - Creates transformation record with parameters
2. **PostgreSQL** (if `session_id` and `user_id` provided):
   - Generates embedding for source text
   - Inserts into `transformations` table with status "processing"
   - Columns: `id`, `session_id`, `user_id`, `source_text`, `source_embedding`, `persona`, `namespace`, `style`, `status`, `extra_metadata`

**Side Effects**:
1. **Token Validation**: Checks content against tier-based token limits
2. **Chunking Decision**: Determines if content needs chunking (premium only)
3. **Background Task**: Starts either `process_transformation()` or `process_transformation_chunked()`
4. **Embedding Generation**: Creates vector embedding for source text (if PostgreSQL storage enabled)
5. **Claude API**: Will be called by background task

**Error Cases**:
- `400 Bad Request`: Document exceeds token limit
  ```json
  {
    "detail": {
      "error": "Document exceeds token limit",
      "message": "Content exceeds limit",
      "token_count": 35000,
      "token_limit": 30000,
      "tier": "free"
    }
  }
  ```
- `500 Internal Server Error`: Failed to create transformation

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/transform \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The quick brown fox jumps over the lazy dog.",
    "persona": "Victorian poet",
    "namespace": "19th century literature",
    "style": "creative",
    "preserve_structure": true,
    "depth": 0.7,
    "user_tier": "free",
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174001"
  }'
```

**Example Response**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "created_at": "2025-10-07T14:30:00Z",
  "message": "Transformation started successfully"
}
```

**Chunked Transformation Response** (premium tier, large document):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "created_at": "2025-10-07T14:30:00Z",
  "message": "Transformation started (processing in 3 chunks)"
}
```

**Background Processing**:
- **Single-pass**: `process_transformation()` runs asynchronously
  1. Updates status to "processing" (progress 0.1)
  2. Calls `TransformationAgent.transform()`
  3. Updates storage with transformed content (progress 1.0)
  4. Generates embedding for transformed content (if PostgreSQL enabled)
  5. Updates PostgreSQL status to "completed"

- **Chunked** (premium only): `process_transformation_chunked()` runs asynchronously
  1. Updates status to "processing" (progress 0.05)
  2. Splits content into chunks (preserving paragraphs if `preserve_structure=true`)
  3. Transforms each chunk sequentially (progress 0.1 to 0.9)
  4. Reassembles chunks (double newline if structure preserved, single space otherwise)
  5. Updates storage with final content (progress 1.0)

---

### 4. Get Transformation Status

**HTTP Method & Path**: `GET /api/transform/{transformation_id}`

**Purpose**: Retrieves the current status of a transformation job, including progress, current content, and any errors.

**Parameters**:
- **Path**:
  - `transformation_id` (string, required): Transformation job ID (UUID)

**Response Model**: `TransformationStatus`
- `id` (string): Transformation ID
- `status` (TransformationStatusEnum): Current status - "pending", "processing", "completed", "failed", or "checkpointed"
- `progress` (float): Completion percentage (0.0 to 1.0)
- `original_content` (string): Original input text
- `transformed_content` (string | null): Transformed text (null if not complete)
- `persona` (string): Target persona
- `namespace` (string): Conceptual framework
- `style` (string): Writing style
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp
- `completed_at` (datetime | null): Completion timestamp
- `error` (string | null): Error message if failed
- `checkpoints` (array): List of checkpoint IDs

**Database Queries**:
- **TransformationStorage**: `get_transformation(transformation_id)`
- No PostgreSQL queries

**Side Effects**: None (read-only operation)

**Error Cases**:
- `404 Not Found`: Transformation not found

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/transform/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Example Response (Processing)**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "processing",
  "progress": 0.45,
  "original_content": "The quick brown fox...",
  "transformed_content": null,
  "persona": "Victorian poet",
  "namespace": "19th century literature",
  "style": "creative",
  "created_at": "2025-10-07T14:30:00Z",
  "updated_at": "2025-10-07T14:30:15Z",
  "completed_at": null,
  "error": null,
  "checkpoints": []
}
```

**Example Response (Completed)**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "progress": 1.0,
  "original_content": "The quick brown fox jumps over the lazy dog.",
  "transformed_content": "Lo, the swift russet vulpine doth leap o'er the indolent hound.",
  "persona": "Victorian poet",
  "namespace": "19th century literature",
  "style": "creative",
  "created_at": "2025-10-07T14:30:00Z",
  "updated_at": "2025-10-07T14:30:30Z",
  "completed_at": "2025-10-07T14:30:30Z",
  "error": null,
  "checkpoints": ["cp-001", "cp-002"]
}
```

**Example Response (Failed)**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "failed",
  "progress": 0.3,
  "original_content": "The quick brown fox...",
  "transformed_content": null,
  "persona": "Victorian poet",
  "namespace": "19th century literature",
  "style": "creative",
  "created_at": "2025-10-07T14:30:00Z",
  "updated_at": "2025-10-07T14:30:10Z",
  "completed_at": null,
  "error": "API rate limit exceeded",
  "checkpoints": []
}
```

---

### 5. Get Transformation Result

**HTTP Method & Path**: `GET /api/transform/{transformation_id}/result`

**Purpose**: Retrieves the final result of a completed transformation. Only available for transformations with status "completed".

**Parameters**:
- **Path**:
  - `transformation_id` (string, required): Transformation job ID (UUID)

**Response Model**: `TransformationResult`
- `id` (string): Transformation ID
- `original_content` (string): Original input text
- `transformed_content` (string): Transformed text
- `persona` (string): Target persona
- `namespace` (string): Conceptual framework
- `style` (string): Writing style
- `metadata` (object): Additional metadata (currently empty dict)
- `completed_at` (datetime): Completion timestamp

**Database Queries**:
- **TransformationStorage**: `get_transformation(transformation_id)`
- No PostgreSQL queries

**Side Effects**: None (read-only operation)

**Error Cases**:
- `404 Not Found`: Transformation not found
- `400 Bad Request`: Transformation is not complete
  ```json
  {
    "detail": "Transformation is not complete (status: processing)"
  }
  ```

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/transform/a1b2c3d4-e5f6-7890-abcd-ef1234567890/result
```

**Example Response**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "original_content": "The quick brown fox jumps over the lazy dog.",
  "transformed_content": "Lo, the swift russet vulpine doth leap o'er the indolent hound.",
  "persona": "Victorian poet",
  "namespace": "19th century literature",
  "style": "creative",
  "metadata": {},
  "completed_at": "2025-10-07T14:30:30Z"
}
```

---

### 6. Get Transformation History

**HTTP Method & Path**: `GET /api/history`

**Purpose**: Retrieves a paginated list of recent transformations with their status. Useful for browsing past transformations and monitoring transformation activity.

**Parameters**:
- **Query**:
  - `limit` (integer, optional): Maximum number of results to return (default: `50`)
  - `offset` (integer, optional): Number of results to skip for pagination (default: `0`)

**Response Model**: `List[TransformationStatus]`

**Database Queries**:
- **TransformationStorage**: `get_all_transformations(limit, offset)`
- No PostgreSQL queries

**Side Effects**: None (read-only operation)

**Error Cases**: None (returns empty array if no transformations exist)

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/history?limit=10&offset=0"
```

**Example Response**:
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "progress": 1.0,
    "original_content": "The quick brown fox...",
    "transformed_content": "Lo, the swift russet vulpine...",
    "persona": "Victorian poet",
    "namespace": "19th century literature",
    "style": "creative",
    "created_at": "2025-10-07T14:30:00Z",
    "updated_at": "2025-10-07T14:30:30Z",
    "completed_at": "2025-10-07T14:30:30Z",
    "error": null,
    "checkpoints": ["cp-001"]
  },
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "status": "processing",
    "progress": 0.6,
    "original_content": "Lorem ipsum dolor sit amet...",
    "transformed_content": null,
    "persona": "technical writer",
    "namespace": "software documentation",
    "style": "technical",
    "created_at": "2025-10-07T14:25:00Z",
    "updated_at": "2025-10-07T14:25:45Z",
    "completed_at": null,
    "error": null,
    "checkpoints": []
  }
]
```

**Pagination Example**:
```bash
# First page (items 0-49)
curl -X GET "http://localhost:8000/api/history?limit=50&offset=0"

# Second page (items 50-99)
curl -X GET "http://localhost:8000/api/history?limit=50&offset=50"

# Third page (items 100-149)
curl -X GET "http://localhost:8000/api/history?limit=50&offset=100"
```

---

### 7. Create Checkpoint

**HTTP Method & Path**: `POST /api/transform/{transformation_id}/checkpoint`

**Purpose**: Creates a checkpoint for the current transformation state. This allows rolling back to this point later if needed, supporting iterative refinement workflows.

**Parameters**:
- **Path**:
  - `transformation_id` (string, required): Transformation job ID (UUID)
- **Body** (`CheckpointCreate`):
  - `name` (string, optional): Human-readable checkpoint name

**Response Model**: `CheckpointResponse`
- `checkpoint_id` (string): Unique checkpoint ID
- `name` (string): Checkpoint name
- `created_at` (datetime): Creation timestamp
- `message` (string): Success message

**Database Queries**:
- **TransformationStorage**: `get_transformation(transformation_id)`
- **Agent Checkpoint Storage**: Creates checkpoint in agent's checkpoint system
- No PostgreSQL queries

**Side Effects**:
- Creates checkpoint snapshot via `TransformationAgent.create_checkpoint()`
- Stores current content state (transformed if available, otherwise original)

**Error Cases**:
- `404 Not Found`: Transformation not found
- `500 Internal Server Error`: Failed to create checkpoint

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/transform/a1b2c3d4-e5f6-7890-abcd-ef1234567890/checkpoint \
  -H "Content-Type: application/json" \
  -d '{
    "name": "After first revision"
  }'
```

**Example Response**:
```json
{
  "checkpoint_id": "cp-123e4567-e89b-12d3-a456-426614174000",
  "name": "After first revision",
  "created_at": "2025-10-07T14:35:00Z",
  "message": "Checkpoint created successfully"
}
```

**Auto-generated Name Example**:
```bash
curl -X POST http://localhost:8000/api/transform/a1b2c3d4-e5f6-7890-abcd-ef1234567890/checkpoint \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response**:
```json
{
  "checkpoint_id": "cp-123e4567-e89b-12d3-a456-426614174000",
  "name": "checkpoint_20251007_143500",
  "created_at": "2025-10-07T14:35:00Z",
  "message": "Checkpoint created successfully"
}
```

---

### 8. Rollback Transformation

**HTTP Method & Path**: `POST /api/transform/{transformation_id}/rollback`

**Purpose**: Rolls back a transformation to a previous checkpoint, restoring the content state to the specified checkpoint. Updates transformation status to "checkpointed".

**Parameters**:
- **Path**:
  - `transformation_id` (string, required): Transformation job ID (UUID)
- **Body** (`RollbackRequest`):
  - `checkpoint_id` (string, required): Checkpoint ID to restore

**Response Model**: JSON object (no Pydantic schema)
- `success` (boolean): Always `true` on success
- `message` (string): Success message with checkpoint name
- `checkpoint_name` (string): Name of the restored checkpoint

**Database Queries**:
- **Agent Checkpoint Storage**: Retrieves checkpoint data
- **TransformationStorage**: Updates transformation with rolled-back content and status "checkpointed"
- No PostgreSQL queries

**Side Effects**:
- Restores transformation content to checkpoint state via `TransformationAgent.rollback_to_checkpoint()`
- Updates transformation status to "checkpointed"
- Content may differ from current state (destructive operation)

**Error Cases**:
- `400 Bad Request`: Rollback failed (invalid checkpoint, checkpoint not found, etc.)

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/transform/a1b2c3d4-e5f6-7890-abcd-ef1234567890/rollback \
  -H "Content-Type: application/json" \
  -d '{
    "checkpoint_id": "cp-123e4567-e89b-12d3-a456-426614174000"
  }'
```

**Example Response**:
```json
{
  "success": true,
  "message": "Rolled back to checkpoint: After first revision",
  "checkpoint_name": "After first revision"
}
```

**Error Response**:
```json
{
  "detail": "Checkpoint not found"
}
```

**Workflow Example**:
```bash
# 1. Create transformation
POST /api/transform
# Returns: { "id": "trans-001", ... }

# 2. Check status until complete
GET /api/transform/trans-001
# Returns: { "status": "completed", "transformed_content": "Version 1", ... }

# 3. Create checkpoint
POST /api/transform/trans-001/checkpoint
# Returns: { "checkpoint_id": "cp-001", ... }

# 4. Continue editing/transforming...
# (Make changes to transformation)

# 5. Not happy with changes? Rollback!
POST /api/transform/trans-001/rollback
# Body: { "checkpoint_id": "cp-001" }
# Returns: { "success": true, "checkpoint_name": "...", ... }

# 6. Verify restoration
GET /api/transform/trans-001
# Returns: { "status": "checkpointed", "transformed_content": "Version 1", ... }
```

---

### 9. Delete Transformation

**HTTP Method & Path**: `DELETE /api/transform/{transformation_id}`

**Purpose**: Permanently deletes a transformation and all associated data including checkpoints.

**Parameters**:
- **Path**:
  - `transformation_id` (string, required): Transformation job ID (UUID)

**Response Model**: JSON object (no Pydantic schema)
- `success` (boolean): Always `true` on success
- `message` (string): Success message

**Database Queries**:
- **TransformationStorage**: `delete_transformation(transformation_id)`
- **Note**: Does NOT delete from PostgreSQL (only legacy storage)

**Side Effects**:
- Permanently deletes transformation record
- Deletes all associated checkpoints
- Cannot be undone

**Error Cases**:
- `404 Not Found`: Transformation not found

**Example Request**:
```bash
curl -X DELETE http://localhost:8000/api/transform/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Example Response**:
```json
{
  "success": true,
  "message": "Transformation deleted"
}
```

**Important Notes**:
- This operation is **irreversible**
- Only deletes from legacy `TransformationStorage` system
- PostgreSQL records are **NOT deleted** by this endpoint
- To delete PostgreSQL records, use the Library API endpoints

---

### 10. Analyze Content

**HTTP Method & Path**: `POST /api/analyze`

**Purpose**: Analyzes content to extract its inherent characteristics including persona, namespace, style, tone, and structure. Useful for understanding the current state of content before applying transformations.

**Parameters**:
- **Body** (JSON):
  - `content` (string, required): Text content to analyze (sent as raw string, not in JSON object)

**Note**: This endpoint accepts the content as a direct string parameter, not wrapped in a JSON object.

**Response Model**: JSON object (no Pydantic schema)
- Returned by `TransformationAgent.analyze_content()`
- Contains extracted characteristics like:
  - `persona`: Detected persona/voice
  - `namespace`: Identified domain/framework
  - `style`: Writing style characteristics
  - `tone`: Emotional tone
  - `structure`: Content structure analysis
  - Additional analysis fields

**Database Queries**: None

**Side Effects**:
- Calls Claude API via `TransformationAgent.analyze_content()`
- Consumes API tokens

**Error Cases**:
- `500 Internal Server Error`: Analysis failed (includes error details from agent)

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '"The quantum entanglement phenomenon demonstrates the non-local nature of particle correlations, challenging classical intuitions about causality and locality in physical systems."'
```

**Example Response**:
```json
{
  "persona": "academic physicist",
  "namespace": "quantum mechanics",
  "style": "academic",
  "tone": "formal, explanatory",
  "structure": "single complex sentence with technical terminology",
  "technical_level": "advanced",
  "audience": "physics researchers or advanced students",
  "key_concepts": ["quantum entanglement", "non-locality", "causality"],
  "suggested_transformations": {
    "for_general_audience": {
      "persona": "science communicator",
      "namespace": "popular science",
      "style": "casual"
    },
    "for_technical_documentation": {
      "persona": "technical writer",
      "namespace": "quantum computing",
      "style": "technical"
    }
  }
}
```

**Use Cases**:
1. **Pre-transformation Analysis**: Understand content before transforming
2. **Style Detection**: Identify current writing style
3. **Audience Matching**: Determine if content matches target audience
4. **Transformation Suggestions**: Get recommendations for transformations

**Error Response**:
```json
{
  "detail": "Analysis failed: API request timeout"
}
```

---

## Background Task Functions

These are internal functions called as background tasks. They are not directly accessible via HTTP but are essential to understanding the transformation flow.

### process_transformation()

**Purpose**: Background task to process a single-pass transformation.

**Parameters**:
- `transformation_id` (string): Transformation job ID
- `request` (TransformationRequest): Original transformation request

**Flow**:
1. Update status to "processing" (progress 0.1)
2. Call `TransformationAgent.transform()` with all parameters
3. On success:
   - Update TransformationStorage with transformed content (progress 1.0, status "completed")
   - Generate embedding for transformed content
   - Update PostgreSQL record (if session/user provided)
4. On failure:
   - Update TransformationStorage with error (status "failed")
   - Update PostgreSQL record (if session/user provided)

**Database Operations**:
- TransformationStorage: Updates status and content
- PostgreSQL: Updates `transformations` table with result and embedding

**Claude API Calls**: One call to `transform()`

---

### process_transformation_chunked()

**Purpose**: Background task to process transformation with chunking (premium tier only).

**Parameters**:
- `transformation_id` (string): Transformation job ID
- `request` (TransformationRequest): Original transformation request
- `num_chunks` (int): Number of chunks to split content into

**Flow**:
1. Update status to "processing" (progress 0.05)
2. Create `TextChunker` instance
3. Split content into chunks:
   - If `preserve_structure=true`: Split by paragraphs
   - Otherwise: Split by token count
4. For each chunk:
   - Update progress (0.1 to 0.9 incrementally)
   - Transform chunk via `TransformationAgent.transform()`
   - If chunk fails: Fail entire transformation
5. Reassemble chunks:
   - If `preserve_structure=true`: Join with `\n\n`
   - Otherwise: Join with single space
6. Update TransformationStorage with final content (progress 1.0, status "completed")

**Database Operations**:
- TransformationStorage: Updates status and content
- PostgreSQL: NOT updated (chunked transformations use legacy storage only)

**Claude API Calls**: One call per chunk (e.g., 3 chunks = 3 API calls)

**Chunking Strategy**:
- **Premium tier only**: Free tier cannot use chunking
- **Max chunk size**: ~40,000 tokens per chunk
- **Paragraph preservation**: Attempts to split at paragraph boundaries when `preserve_structure=true`
- **Progress tracking**: Granular progress updates per chunk

---

## Data Models

### TransformationRequest
```python
{
  "content": str,                    # Required - Text to transform
  "persona": str,                    # Required - Target persona
  "namespace": str,                  # Required - Conceptual framework
  "style": TransformationStyle,      # Required - Writing style enum
  "preserve_structure": bool,        # Optional - Default: true
  "depth": float,                    # Optional - Range: 0.0-1.0, Default: 0.5
  "user_tier": str,                  # Optional - "free" or "premium", Default: "free"
  "session_id": str | null,          # Optional - UUID for session linking
  "user_id": str | null              # Optional - UUID for user linking
}
```

### TransformationStyle (Enum)
```python
{
  "FORMAL": "formal",
  "CASUAL": "casual",
  "ACADEMIC": "academic",
  "CREATIVE": "creative",
  "TECHNICAL": "technical",
  "JOURNALISTIC": "journalistic"
}
```

### TransformationStatusEnum (Enum)
```python
{
  "PENDING": "pending",           # Initial state
  "PROCESSING": "processing",     # Transformation in progress
  "COMPLETED": "completed",       # Transformation finished successfully
  "FAILED": "failed",            # Transformation failed
  "CHECKPOINTED": "checkpointed" # Rolled back to checkpoint
}
```

### TransformationResponse
```python
{
  "id": str,                      # UUID of transformation job
  "status": TransformationStatusEnum,
  "created_at": datetime,
  "message": str
}
```

### TransformationStatus
```python
{
  "id": str,
  "status": TransformationStatusEnum,
  "progress": float,              # 0.0 to 1.0
  "original_content": str,
  "transformed_content": str | null,
  "persona": str,
  "namespace": str,
  "style": str,
  "created_at": datetime,
  "updated_at": datetime,
  "completed_at": datetime | null,
  "error": str | null,
  "checkpoints": list[str]        # List of checkpoint IDs
}
```

### TransformationResult
```python
{
  "id": str,
  "original_content": str,
  "transformed_content": str,     # Never null (only returned when completed)
  "persona": str,
  "namespace": str,
  "style": str,
  "metadata": dict,
  "completed_at": datetime
}
```

### CheckpointCreate
```python
{
  "name": str | null              # Optional checkpoint name
}
```

### CheckpointResponse
```python
{
  "checkpoint_id": str,
  "name": str,
  "created_at": datetime,
  "message": str
}
```

### RollbackRequest
```python
{
  "checkpoint_id": str            # Required - Checkpoint to restore
}
```

---

## Database Schema

### PostgreSQL Table: `transformations`

**Columns**:
- `id` (UUID): Primary key
- `session_id` (UUID): Foreign key to `sessions.id` (CASCADE on delete)
- `user_id` (UUID): Foreign key to `users.id` (CASCADE on delete)
- `source_text` (TEXT): Original content
- `source_embedding` (VECTOR(1536)): Embedding of source text
- `persona` (VARCHAR(100)): Target persona
- `namespace` (VARCHAR(100)): Conceptual framework
- `style` (VARCHAR(100)): Writing style
- `transformed_content` (TEXT): Transformed text (nullable)
- `transformed_embedding` (VECTOR(1536)): Embedding of transformed text (nullable)
- `belief_framework` (JSONB): Philosophical metadata (nullable)
- `emotional_profile` (TEXT): Emotional analysis (nullable)
- `philosophical_context` (TEXT): Philosophical context (nullable)
- `status` (VARCHAR(50)): "pending", "processing", "completed", "failed"
- `error_message` (TEXT): Error details (nullable)
- `tokens_used` (INTEGER): API token count (nullable)
- `processing_time_ms` (INTEGER): Processing duration (nullable)
- `created_at` (TIMESTAMP WITH TIMEZONE): Creation time
- `completed_at` (TIMESTAMP WITH TIMEZONE): Completion time (nullable)
- `parent_transformation_id` (UUID): Parent transformation (for lineage)
- `is_checkpoint` (BOOLEAN): Whether this is a checkpoint
- `metadata` (JSONB): Extra metadata (column name, aliased as `extra_metadata` in model)

**Indexes**:
- Primary key on `id`
- Foreign key on `session_id`
- Foreign key on `user_id`
- Vector index on `source_embedding` (for similarity search)
- Vector index on `transformed_embedding` (for similarity search)

**Relationships**:
- `session`: Many-to-one with `sessions`
- `user`: Many-to-one with `users`
- `parent`: Self-referential (transformation lineage)
- `children`: Backref from parent (transformation tree)

---

## Storage Architecture

### Dual Storage System

The transformation API uses **two separate storage systems**:

1. **Legacy TransformationStorage** (File-based or Redis):
   - Used for all transformations
   - Stores transformation state, progress, checkpoints
   - Accessed via `utils/storage.py`
   - **All endpoints read from this system**

2. **PostgreSQL Database**:
   - Optional (requires `session_id` and `user_id`)
   - Stores embeddings for semantic search
   - Integrates with session/user system
   - Used for provenance tracking and lineage
   - Updated in background tasks

**Why Dual Storage?**
- Legacy system provides fast, simple transformation tracking
- PostgreSQL provides rich querying, embeddings, and user integration
- Transition strategy: New features use PostgreSQL, old features use legacy storage

**Consistency Note**:
- Both systems updated independently
- No transactions across both systems
- PostgreSQL failures don't break transformations
- Legacy storage is source of truth for transformation state

---

## Token Management

### Token Limits by Tier

**Free Tier**:
- Input: 30,000 tokens (~22,500 words)
- Output: 10,000 tokens (~7,500 words)
- Chunking: **NOT ALLOWED**

**Premium Tier**:
- Input: 150,000 tokens (~112,500 words)
- Output: 50,000 tokens (~37,500 words)
- Chunking: **ENABLED** (auto-chunks at ~40,000 tokens per chunk)

### Token Checking Flow

1. **Pre-transformation Check** (via `/api/check-tokens`):
   - User can validate before submitting transformation
   - Returns token count, word estimate, and chunking info
   - Non-blocking (informational only)

2. **Transformation Validation** (in `/api/transform`):
   - Enforces token limits
   - Blocks transformation if exceeds tier limit
   - Returns HTTP 400 with detailed error

3. **Chunking Decision**:
   - Premium tier only
   - Automatically chunks if content > 40,000 tokens
   - Preserves paragraphs when `preserve_structure=true`

### Token Estimation

**Conversion Factors**:
- 1 token ≈ 0.75 words (English)
- 1 token ≈ 4 characters (English)

**Calculation Method**:
- Uses `tiktoken` library with `cl100k_base` encoding (GPT-4 tokenizer)
- Exact token count for Claude models

---

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful request
- **400 Bad Request**:
  - Token limit exceeded
  - Transformation not complete (when requesting result)
  - Rollback failed
- **404 Not Found**:
  - Transformation not found
- **500 Internal Server Error**:
  - Token check failed
  - Transformation creation failed
  - Checkpoint creation failed
  - Analysis failed

### Error Response Format

**Standard Error** (from FastAPI):
```json
{
  "detail": "Error message here"
}
```

**Token Limit Error** (structured):
```json
{
  "detail": {
    "error": "Document exceeds token limit",
    "message": "Content exceeds free tier input limit of 30,000 tokens",
    "token_count": 35000,
    "token_limit": 30000,
    "tier": "free"
  }
}
```

**Test Endpoint Error**:
```json
{
  "error": "Error message",
  "traceback": "Full Python traceback..."
}
```

---

## Transformation Workflow Examples

### Basic Transformation Workflow

```bash
# 1. Check tokens (optional but recommended)
curl -X POST http://localhost:8000/api/check-tokens \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your content here...",
    "user_tier": "free"
  }'
# Response: { "is_within_limit": true, "token_count": 1000, ... }

# 2. Create transformation
curl -X POST http://localhost:8000/api/transform \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your content here...",
    "persona": "technical writer",
    "namespace": "software documentation",
    "style": "technical",
    "user_tier": "free"
  }'
# Response: { "id": "trans-123", "status": "pending", ... }

# 3. Poll status until complete
curl -X GET http://localhost:8000/api/transform/trans-123
# Response: { "status": "processing", "progress": 0.5, ... }

# ... wait and poll again ...
curl -X GET http://localhost:8000/api/transform/trans-123
# Response: { "status": "completed", "progress": 1.0, "transformed_content": "...", ... }

# 4. Get final result
curl -X GET http://localhost:8000/api/transform/trans-123/result
# Response: { "transformed_content": "Final transformed text...", ... }
```

### Checkpoint and Rollback Workflow

```bash
# 1. Create transformation (as above)
# ... transformation completes ...

# 2. Create checkpoint before making changes
curl -X POST http://localhost:8000/api/transform/trans-123/checkpoint \
  -H "Content-Type: application/json" \
  -d '{ "name": "Before edits" }'
# Response: { "checkpoint_id": "cp-001", ... }

# 3. Make further transformations/edits
# (Apply additional transformations or manual edits)

# 4. Not happy? Rollback to checkpoint
curl -X POST http://localhost:8000/api/transform/trans-123/rollback \
  -H "Content-Type: application/json" \
  -d '{ "checkpoint_id": "cp-001" }'
# Response: { "success": true, "checkpoint_name": "Before edits", ... }

# 5. Verify rollback
curl -X GET http://localhost:8000/api/transform/trans-123
# Response: { "status": "checkpointed", "transformed_content": "Original content from checkpoint", ... }
```

### Chunked Transformation Workflow (Premium)

```bash
# 1. Check if chunking needed
curl -X POST http://localhost:8000/api/check-tokens \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Very long content (100,000 tokens)...",
    "user_tier": "premium"
  }'
# Response: { "needs_chunking": true, "num_chunks": 3, ... }

# 2. Create transformation (automatically chunks)
curl -X POST http://localhost:8000/api/transform \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Very long content...",
    "persona": "academic",
    "namespace": "research",
    "style": "academic",
    "preserve_structure": true,
    "user_tier": "premium"
  }'
# Response: { "id": "trans-456", "message": "Transformation started (processing in 3 chunks)", ... }

# 3. Monitor progress (shows chunk-by-chunk progress)
curl -X GET http://localhost:8000/api/transform/trans-456
# Response: { "status": "processing", "progress": 0.33, ... }  # Chunk 1 done
# ... { "status": "processing", "progress": 0.66, ... }  # Chunk 2 done
# ... { "status": "completed", "progress": 1.0, ... }   # All chunks done
```

### Content Analysis Workflow

```bash
# 1. Analyze existing content
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '"The implementation leverages a distributed microservices architecture with event-driven communication patterns."'
# Response: {
#   "persona": "software architect",
#   "namespace": "system design",
#   "style": "technical",
#   "suggested_transformations": { ... }
# }

# 2. Use analysis to inform transformation
curl -X POST http://localhost:8000/api/transform \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The implementation leverages...",
    "persona": "product manager",
    "namespace": "business strategy",
    "style": "casual"
  }'
# Transforms from technical architect voice to PM voice
```

---

## Integration Notes

### Session and User Integration

**When to provide `session_id` and `user_id`**:
- **Required for**:
  - Storing transformations in PostgreSQL
  - Generating embeddings
  - Linking transformations to conversations
  - Provenance tracking

- **Optional if**:
  - Using standalone transformation API
  - Only need transformation result (no persistence)
  - Testing or one-off transformations

**Example with Session Integration**:
```json
{
  "content": "Transform this text",
  "persona": "poet",
  "namespace": "literature",
  "style": "creative",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**PostgreSQL Benefits**:
- Semantic search across transformations
- User transformation history
- Session-based transformation chains
- Lineage tracking (parent/child relationships)

### Claude Agent SDK

**Model Used**: `claude-3-5-sonnet-20241022`

**Agent Capabilities**:
- `transform()`: Main transformation function
- `analyze_content()`: Content analysis
- `create_checkpoint()`: Checkpoint creation
- `rollback_to_checkpoint()`: Checkpoint restoration

**API Consumption**:
- Single transformation: 1 API call
- Chunked transformation: N API calls (1 per chunk)
- Analysis: 1 API call
- Checkpoints: No API calls (local storage)
- Rollback: No API calls (local retrieval)

---

## Performance Considerations

### Transformation Speed

**Factors affecting speed**:
1. **Content length**: Longer content = longer processing
2. **Chunking**: Chunked transformations take longer (sequential processing)
3. **Claude API response time**: Typically 2-10 seconds per call
4. **Embedding generation**: Adds 1-2 seconds (if PostgreSQL enabled)

**Expected timings**:
- Short text (< 1,000 tokens): 3-5 seconds
- Medium text (1,000-10,000 tokens): 5-15 seconds
- Long text (10,000-30,000 tokens): 15-30 seconds
- Chunked (100,000 tokens, 3 chunks): 45-90 seconds

### Polling Recommendations

**Status polling**:
- Poll interval: 2-3 seconds
- Exponential backoff for long transformations
- Watch `progress` field for accurate status

**Example polling logic**:
```javascript
async function pollTransformation(id) {
  let attempts = 0;
  while (attempts < 100) {
    const status = await fetch(`/api/transform/${id}`);
    const data = await status.json();

    if (data.status === 'completed') return data;
    if (data.status === 'failed') throw new Error(data.error);

    // Exponential backoff: 2s, 3s, 5s, 8s, ...
    const delay = Math.min(2000 + (attempts * 1000), 10000);
    await sleep(delay);
    attempts++;
  }
  throw new Error('Transformation timeout');
}
```

### Caching

**No caching implemented**:
- Each transformation is unique
- No memoization of Claude API calls
- TransformationStorage is already fast (in-memory or Redis)

**Potential optimizations**:
- Cache analysis results for identical content
- Reuse embeddings for duplicate source texts
- Store common transformation patterns

---

## Security Considerations

### Input Validation

**Validated fields**:
- `depth`: Must be 0.0 to 1.0
- `style`: Must be valid `TransformationStyle` enum value
- `user_tier`: Validated indirectly via token limits

**NOT validated**:
- `content`: No length limit check (handled by token limits)
- `persona`, `namespace`: No validation (user-defined)
- `checkpoint_id`, `transformation_id`: No format validation

### Token Limit Enforcement

**Security purpose**:
- Prevents abuse (sending massive documents)
- Controls API costs
- Ensures fair usage across tiers

**Bypass potential**:
- User can change `user_tier` in request (NO AUTHENTICATION)
- **VULNERABILITY**: No verification of user's actual tier
- **Recommendation**: Add authentication and tier verification

### Data Persistence

**Sensitive data**:
- All content stored in plain text (no encryption)
- Transformations may contain PII
- Checkpoints store full content snapshots

**Recommendations**:
- Add encryption at rest for PostgreSQL
- Implement data retention policies
- Add user consent for storage

### API Authentication

**Current state**: **NO AUTHENTICATION**
- All endpoints are public
- Anyone can create transformations
- Anyone can read/delete any transformation by ID

**Recommendations**:
- Add API key authentication
- Implement user-based authorization
- Restrict deletion to transformation owner
- Add rate limiting

---

## Future Enhancements

### Planned Features

1. **Batch Transformations**: Transform multiple documents in one request
2. **Streaming Responses**: Stream transformation results as they're generated
3. **Custom Styles**: User-defined style templates
4. **Transformation Presets**: Saved persona/namespace/style combinations
5. **Diff View**: Show changes between original and transformed content
6. **Multi-language Support**: Detect and transform across languages

### Potential Improvements

1. **WebSocket Status Updates**: Real-time progress instead of polling
2. **Transformation Templates**: Pre-built transformation configurations
3. **A/B Testing**: Generate multiple variations of a transformation
4. **Quality Scoring**: Automatically score transformation quality
5. **Undo/Redo Stack**: Beyond checkpoints, full history navigation
6. **Collaborative Editing**: Multiple users working on same transformation

### API Versioning

**Current version**: v1 (implicit, no versioning)

**Recommendation**:
- Add `/api/v1/transform` versioning
- Maintain backward compatibility
- Document breaking changes

---

## Related Documentation

- **Pipeline API**: `/Users/tem/humanizer-agent/backend/API_PIPELINE.md` - Batch transformation jobs
- **Vision API**: `/Users/tem/humanizer-agent/backend/API_VISION.md` - Image analysis and OCR
- **Library API**: `/Users/tem/humanizer-agent/backend/API_LIBRARY.md` - Conversation archives
- **Book Builder API**: (Future documentation) - Book creation and editing

---

## Changelog

### 2025-10-07
- Initial comprehensive documentation created
- Documented all 10 endpoints with examples
- Added token management, error handling, and workflow examples
- Included security considerations and future enhancements

---

**Last Updated**: October 7, 2025
**Documented by**: Claude Code
**Total Endpoints**: 10
**Total Lines of Code**: 567
