# Vision Routes API Documentation

## Overview

The Vision API provides endpoints for image upload, Apple Photos integration, and Claude Vision operations (OCR, image description, image analysis). These routes support both synchronous direct operations and asynchronous job-based processing via the transformation pipeline.

**Base Path**: `/api/vision`

**Total Endpoints**: 11

---

## Table of Contents

1. [Image Upload Endpoints](#image-upload-endpoints)
   - [POST /upload](#1-post-apivisionupload)
   - [POST /upload-bulk](#2-post-apivisionupload-bulk)
2. [Vision Job Endpoints](#vision-job-endpoints)
   - [POST /jobs](#3-post-apivisionjobs)
   - [GET /jobs/{job_id}](#4-get-apivisionjobsjob_id)
3. [Direct Vision Operations](#direct-vision-operations)
   - [POST /ocr-direct](#5-post-apivisionocr-direct)
4. [Apple Photos Integration](#apple-photos-integration)
   - [GET /apple-photos/available](#6-get-apivisionapple-photosavailable)
   - [GET /apple-photos/albums](#7-get-apivisionapple-photosalbums)
   - [POST /apple-photos/export-album](#8-post-apivisionapple-photosexport-album)
   - [POST /apple-photos/export-recent](#9-post-apivisionapple-photosexport-recent)

---

## Image Upload Endpoints

### 1. POST /api/vision/upload

**Purpose**: Upload a single image file, extract metadata (including AI generation metadata), and create media + chunk records.

**HTTP Method**: POST (multipart/form-data)

**Parameters**:
- `file` (form-data, required): Image file (PNG, JPEG, JPG, WEBP, GIF)
- `user_id` (form-data, required): User ID for tracking
- `collection_id` (form-data, optional): Link image to a collection/conversation
- `message_id` (form-data, optional): Link image to a specific message

**Response Model**: `dict`

```python
{
    "media_id": str,           # File ID (file-XXX format)
    "chunk_id": str,           # Chunk UUID
    "storage_path": str,       # Path where file is stored
    "thumbnail_url": str,      # URL to retrieve file
    "file_size": int,          # Size in bytes
    "content_type": str,       # MIME type
    "width": Optional[int],    # Image width in pixels
    "height": Optional[int],   # Image height in pixels
    "prompt": Optional[str],   # AI generation prompt (if detected)
    "generator": Optional[str], # AI generator (DALL-E, Stable Diffusion, Midjourney)
    "has_metadata": bool       # Whether EXIF metadata was found
}
```

**Database Queries**:
- `INSERT INTO Media` - Create media record
- `INSERT INTO Chunk` - Create image chunk with asset pointer

**Side Effects**:
- Writes file to `backend/media/uploads/{file_id}.{ext}`
- Extracts image metadata using PIL/Pillow (ImageMetadataExtractor service)
- Detects AI generation metadata (DALL-E, Stable Diffusion, Midjourney prompts)
- Extracts EXIF metadata (camera, GPS, timestamps)
- Creates directory `backend/media/uploads/` if it doesn't exist

**Error Cases**:
- 400: Invalid file type (not in allowed_types: png, jpeg, jpg, webp, gif)
- 500: Upload failed (file write error, metadata extraction error, database error)

**Example Request**:
```http
POST /api/vision/upload
Content-Type: multipart/form-data

file: [binary image data]
user_id: "user-123"
collection_id: "123e4567-e89b-12d3-a456-426614174000"
message_id: "msg-456"
```

**Example Response**:
```json
{
  "media_id": "file-a1b2c3d4e5f6g7h8i9j0k1l2",
  "chunk_id": "123e4567-e89b-12d3-a456-426614174111",
  "storage_path": "backend/media/uploads/file-a1b2c3d4e5f6g7h8i9j0k1l2.png",
  "thumbnail_url": "/api/library/media/file-a1b2c3d4e5f6g7h8i9j0k1l2",
  "file_size": 245678,
  "content_type": "image/png",
  "width": 1024,
  "height": 1024,
  "prompt": "A serene mountain landscape at sunset",
  "generator": "DALL-E 3",
  "has_metadata": true
}
```

**Notes**:
- File ID format: `file-{24-char-hex}`
- Chunk content stored as JSON string with image_asset_pointer structure
- AI metadata detection supports:
  - **DALL-E**: `parameters.prompt` field
  - **Stable Diffusion**: `parameters.prompt` field
  - **Midjourney**: `/imagine prompt:` in EXIF comments
- `platform` field set to generator name if detected, otherwise "upload"
- `extra_metadata` includes: uploaded_by, format, mode, exif, ai_metadata, created_date, camera

---

### 2. POST /api/vision/upload-bulk

**Purpose**: Upload multiple images at once (supports folder imports) with batch processing.

**HTTP Method**: POST (multipart/form-data)

**Parameters**:
- `files` (form-data, required): List of image files
- `user_id` (form-data, required): User ID for tracking
- `collection_id` (form-data, optional): Link all images to this collection

**Response Model**: `dict`

```python
{
    "uploaded": List[dict],      # Successfully uploaded files
    "failed": List[dict],        # Failed uploads with errors
    "total": int,                # Total files attempted
    "success_count": int,        # Number of successful uploads
    "fail_count": int            # Number of failed uploads
}
```

**Database Queries**:
- For each file:
  - `INSERT INTO Media` - Create media record
  - `INSERT INTO Chunk` - Create image chunk
- `COMMIT` after each file (individual transactions)

**Side Effects**:
- Writes files to `backend/media/uploads/{file_id}.{ext}`
- Extracts metadata for each file using ImageMetadataExtractor
- Creates directory `backend/media/uploads/` if it doesn't exist
- Continues processing on individual file failures (partial success)

**Error Cases**:
- None (endpoint always returns 200 with success/failure breakdown)
- Individual file errors captured in `failed` array

**Example Request**:
```http
POST /api/vision/upload-bulk
Content-Type: multipart/form-data

files: [image1.png, image2.jpg, image3.webp]
user_id: "user-123"
collection_id: "123e4567-e89b-12d3-a456-426614174000"
```

**Example Response**:
```json
{
  "uploaded": [
    {
      "media_id": "file-a1b2c3d4e5f6g7h8i9j0k1l2",
      "filename": "image1.png",
      "prompt": "A mountain landscape",
      "generator": "DALL-E 3"
    },
    {
      "media_id": "file-x9y8z7w6v5u4t3s2r1q0p9o8",
      "filename": "image2.jpg",
      "prompt": null,
      "generator": null
    }
  ],
  "failed": [
    {
      "filename": "image3.webp",
      "error": "Invalid file format"
    }
  ],
  "total": 3,
  "success_count": 2,
  "fail_count": 1
}
```

**Notes**:
- Each file processed independently (one failure doesn't stop others)
- No message_id parameter (bulk uploads not linked to specific messages)
- Reuses single upload logic inline for each file
- Errors logged but don't halt processing

---

## Vision Job Endpoints

### 3. POST /api/vision/jobs

**Purpose**: Create a vision processing job for background execution (OCR, description, analysis, diagram extraction).

**HTTP Method**: POST (application/json)

**Request Model**: `VisionJobCreate`

```python
class VisionJobCreate(BaseModel):
    media_id: str                    # Media file ID (file-XXX format)
    job_type: str                    # vision_ocr, vision_describe, vision_analyze, vision_diagram
    prompt: Optional[str] = None     # Custom prompt for vision operation
    add_to_collection: bool = True   # Add result to source collection
```

**Response Model**: `VisionJobResponse`

```python
class VisionJobResponse(BaseModel):
    job_id: str                      # New job UUID
    status: str                      # Job status (always "pending" on creation)
    job_type: str                    # Job type (echoed from request)
    media_id: str                    # Media ID (echoed from request)
    result_chunk_id: Optional[str]   # Always None on creation
```

**Database Queries**:
- `SELECT FROM Media WHERE original_media_id = media_id` - Find media record
- `SELECT FROM Chunk WHERE chunk_type = 'image' AND content CONTAINS media_id LIMIT 1` - Find source chunk
- `INSERT INTO TransformationJob` - Create job record

**Side Effects**:
- Creates TransformationJob with status "pending"
- Job will be picked up by background processor for async execution
- Job parameters stored in `parameters` JSON field

**Error Cases**:
- 400: Invalid job type (not in valid_types: vision_ocr, vision_describe, vision_analyze, vision_diagram)
- 404: Media not found (media_id doesn't exist)
- 404: Image chunk not found (no chunk references this media_id)

**Example Request**:
```http
POST /api/vision/jobs
Content-Type: application/json

{
  "media_id": "file-a1b2c3d4e5f6g7h8i9j0k1l2",
  "job_type": "vision_ocr",
  "prompt": "Extract all text from this image",
  "add_to_collection": true
}
```

**Example Response**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174222",
  "status": "pending",
  "job_type": "vision_ocr",
  "media_id": "file-a1b2c3d4e5f6g7h8i9j0k1l2",
  "result_chunk_id": null
}
```

**Notes**:
- Valid job types:
  - `vision_ocr`: Extract text from image using Claude Vision
  - `vision_describe`: Generate detailed image description
  - `vision_analyze`: Analyze image content (objects, scene, composition)
  - `vision_diagram`: Extract structured information from diagrams/charts
- Job parameters include: media_id, prompt, add_to_collection
- Background processor will execute job and update status to "completed" or "failed"

---

### 4. GET /api/vision/jobs/{job_id}

**Purpose**: Get status and result of a vision processing job.

**HTTP Method**: GET

**Parameters**:
- `job_id` (path, required): Job UUID

**Response Model**: `dict`

```python
{
    "id": str,                      # Job UUID
    "status": str,                  # pending, in_progress, completed, failed
    "job_type": str,                # vision_ocr, vision_describe, etc.
    "source_chunk_id": Optional[str], # Source image chunk UUID
    "result_chunk_id": Optional[str], # Result chunk UUID (if completed)
    "created_at": Optional[str],    # ISO 8601 timestamp
    "updated_at": Optional[str],    # ISO 8601 timestamp
    "error": Optional[str],         # Error message (if failed)
    "parameters": dict,             # Job parameters
    "result": Optional[dict],       # Result data (if completed)
    "result_content": Optional[str] # Result chunk content (if completed)
}
```

**Database Queries**:
- `SELECT FROM TransformationJob WHERE id = job_id` - Get job record
- If result_chunk_id exists: `SELECT FROM Chunk WHERE id = result_chunk_id` - Get result chunk

**Side Effects**: None

**Error Cases**:
- 400: Invalid job ID format (not a valid UUID)
- 404: Job not found

**Example Request**:
```http
GET /api/vision/jobs/123e4567-e89b-12d3-a456-426614174222
```

**Example Response (Completed)**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174222",
  "status": "completed",
  "job_type": "vision_ocr",
  "source_chunk_id": "123e4567-e89b-12d3-a456-426614174111",
  "result_chunk_id": "123e4567-e89b-12d3-a456-426614174333",
  "created_at": "2025-10-07T12:00:00",
  "updated_at": "2025-10-07T12:00:45",
  "error": null,
  "parameters": {
    "media_id": "file-a1b2c3d4e5f6g7h8i9j0k1l2",
    "prompt": "Extract all text from this image",
    "add_to_collection": true
  },
  "result": {
    "text": "Extracted text from image...",
    "confidence": 0.95
  },
  "result_content": "Extracted text from image with high confidence..."
}
```

**Example Response (Failed)**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174222",
  "status": "failed",
  "job_type": "vision_ocr",
  "source_chunk_id": "123e4567-e89b-12d3-a456-426614174111",
  "result_chunk_id": null,
  "created_at": "2025-10-07T12:00:00",
  "updated_at": "2025-10-07T12:00:30",
  "error": "Claude API error: Rate limit exceeded",
  "parameters": {
    "media_id": "file-a1b2c3d4e5f6g7h8i9j0k1l2",
    "prompt": "Extract all text from this image",
    "add_to_collection": true
  }
}
```

**Notes**:
- Result data only included if status = "completed"
- Result chunk content only included if result_chunk_id exists
- Polling this endpoint allows frontend to track job progress

---

## Direct Vision Operations

### 5. POST /api/vision/ocr-direct

**Purpose**: Perform OCR directly (synchronous, no job queue) using Claude Vision API.

**HTTP Method**: POST

**Parameters**:
- `media_id` (query, required): Media file ID
- `prompt` (query, optional): Custom OCR prompt for Claude Vision

**Response Model**: `dict` (from VisionService.ocr_image)

```python
{
    "text": str,              # Extracted text
    "confidence": float,      # Confidence score (0-1)
    "metadata": dict          # Additional OCR metadata
}
```

**Database Queries**:
- `SELECT FROM Media WHERE original_media_id = media_id` - Find media record

**Side Effects**:
- Calls Claude Vision API synchronously (blocks request)
- Reads image file from storage_path
- Uses VisionService for Claude API interaction

**Error Cases**:
- 404: Media not found
- 404: Media file not found (storage_path is null/empty)
- 500: OCR failed (Claude API error, file read error)

**Example Request**:
```http
POST /api/vision/ocr-direct?media_id=file-a1b2c3d4e5f6g7h8i9j0k1l2&prompt=Extract%20all%20text
```

**Example Response**:
```json
{
  "text": "Chapter 1: Introduction\n\nThis chapter covers the fundamentals of...",
  "confidence": 0.95,
  "metadata": {
    "model": "claude-3-sonnet",
    "tokens_used": 1250
  }
}
```

**Notes**:
- Use for testing or immediate results
- For production, use POST /jobs with job_type=vision_ocr (async)
- Synchronous operation may timeout on large images or slow API responses
- Requires valid ANTHROPIC_API_KEY in settings
- VisionService initialized with Anthropic client

**Related Services**:
- `VisionService`: Claude Vision API wrapper
- `ImageMetadataExtractor`: Metadata extraction

---

## Apple Photos Integration

### 6. GET /api/vision/apple-photos/available

**Purpose**: Check if Apple Photos is available on this system (macOS only).

**HTTP Method**: GET

**Parameters**: None

**Response Model**: `dict`

```python
{
    "available": bool,      # Whether Apple Photos is accessible
    "platform": bool,       # Whether system is macOS
    "message": str          # Status message
}
```

**Database Queries**: None

**Side Effects**:
- Initializes ApplePhotosService to check system compatibility
- Does not access Photos library (just checks availability)

**Error Cases**: None (always returns 200)

**Example Request**:
```http
GET /api/vision/apple-photos/available
```

**Example Response (macOS)**:
```json
{
  "available": true,
  "platform": true,
  "message": "Apple Photos is available"
}
```

**Example Response (Non-macOS)**:
```json
{
  "available": false,
  "platform": false,
  "message": "Apple Photos not available (macOS only)"
}
```

**Notes**:
- Apple Photos integration only works on macOS
- Uses ApplePhotosService to check Photos library accessibility
- Frontend should call this before showing Apple Photos features

---

### 7. GET /api/vision/apple-photos/albums

**Purpose**: Get list of albums from Apple Photos library with photo counts.

**HTTP Method**: GET

**Parameters**: None

**Response Model**: `dict`

```python
{
    "albums": List[dict],   # List of albums with names and photo counts
    "total_photos": int     # Total photos in library
}
```

**Database Queries**: None (accesses Apple Photos library via AppleScript/SQLite)

**Side Effects**:
- Reads Apple Photos library database (read-only)
- Uses ApplePhotosService to query library

**Error Cases**:
- 400: Apple Photos not available on this system
- 500: Failed to get albums (Photos library access error, permission denied)

**Example Request**:
```http
GET /api/vision/apple-photos/albums
```

**Example Response**:
```json
{
  "albums": [
    {
      "name": "Recents",
      "photo_count": 1234
    },
    {
      "name": "Favorites",
      "photo_count": 56
    },
    {
      "name": "Screenshots",
      "photo_count": 789
    }
  ],
  "total_photos": 5678
}
```

**Notes**:
- Requires macOS and Photos library access permissions
- Album list includes system albums (Recents, Favorites) and user albums
- Photo counts may include videos and other media types

**Related Services**:
- `ApplePhotosService`: macOS Photos library integration

---

### 8. POST /api/vision/apple-photos/export-album

**Purpose**: Export photos from an Apple Photos album to a folder.

**HTTP Method**: POST

**Parameters**:
- `album_name` (query, required): Name of the album to export
- `export_path` (query, required): Path to export photos to
- `limit` (query, optional): Maximum number of photos to export

**Response Model**: `dict`

```python
{
    "status": str,              # "success" or "error"
    "message": str,             # Status message
    "exported_count": int,      # Number of photos exported
    "failed_count": int,        # Number of failed exports
    "export_path": str,         # Path where photos were exported
    "errors": List[str]         # Error messages (if any)
}
```

**Database Queries**: None (accesses Apple Photos library)

**Side Effects**:
- Exports photos from Photos library to filesystem
- Creates export_path directory if it doesn't exist
- Copies photo files (may be large operations)
- Uses ApplePhotosService for export

**Error Cases**:
- 400: Apple Photos not available on this system
- 500: Failed to export album (Photos library error, album not found, filesystem error)

**Example Request**:
```http
POST /api/vision/apple-photos/export-album?album_name=Screenshots&export_path=/tmp/exports&limit=100
```

**Example Response (Success)**:
```json
{
  "status": "success",
  "message": "Exported 100 photos from Screenshots",
  "exported_count": 100,
  "failed_count": 0,
  "export_path": "/tmp/exports",
  "errors": []
}
```

**Example Response (Partial Failure)**:
```json
{
  "status": "success",
  "message": "Exported 95 photos from Screenshots (5 failed)",
  "exported_count": 95,
  "failed_count": 5,
  "export_path": "/tmp/exports",
  "errors": [
    "Failed to export IMG_1234.jpg: File not found",
    "Failed to export IMG_5678.jpg: Permission denied"
  ]
}
```

**Example Response (Error)**:
```json
{
  "status": "error",
  "message": "Album 'NonExistent' not found",
  "exported_count": 0,
  "failed_count": 0,
  "export_path": "/tmp/exports",
  "errors": []
}
```

**Notes**:
- Requires macOS and Photos library access permissions
- Export preserves original filenames and metadata
- Limit parameter useful for testing or partial exports
- Large albums may take significant time to export

**Related Services**:
- `ApplePhotosService`: macOS Photos library integration

---

### 9. POST /api/vision/apple-photos/export-recent

**Purpose**: Export recent photos from Apple Photos library (time-based filter).

**HTTP Method**: POST

**Parameters**:
- `export_path` (query, required): Path to export photos to
- `days` (query, optional): Number of days back to search (default: 30)
- `limit` (query, optional): Maximum number of photos to export (default: 100)

**Response Model**: `dict`

```python
{
    "status": str,              # "success" or "error"
    "message": str,             # Status message
    "exported_count": int,      # Number of photos exported
    "failed_count": int,        # Number of failed exports
    "export_path": str,         # Path where photos were exported
    "date_range": dict,         # Start/end dates for export
    "errors": List[str]         # Error messages (if any)
}
```

**Database Queries**: None (accesses Apple Photos library)

**Side Effects**:
- Exports photos from Photos library to filesystem
- Creates export_path directory if it doesn't exist
- Copies photo files (may be large operations)
- Uses ApplePhotosService for export with date filtering

**Error Cases**:
- 400: Apple Photos not available on this system
- 500: Failed to export recent photos (Photos library error, filesystem error)

**Example Request**:
```http
POST /api/vision/apple-photos/export-recent?export_path=/tmp/recent&days=7&limit=50
```

**Example Response (Success)**:
```json
{
  "status": "success",
  "message": "Exported 50 photos from last 7 days",
  "exported_count": 50,
  "failed_count": 0,
  "export_path": "/tmp/recent",
  "date_range": {
    "start": "2025-09-30T00:00:00",
    "end": "2025-10-07T23:59:59"
  },
  "errors": []
}
```

**Example Response (Fewer Photos Than Limit)**:
```json
{
  "status": "success",
  "message": "Exported 15 photos from last 7 days",
  "exported_count": 15,
  "failed_count": 0,
  "export_path": "/tmp/recent",
  "date_range": {
    "start": "2025-09-30T00:00:00",
    "end": "2025-10-07T23:59:59"
  },
  "errors": []
}
```

**Notes**:
- Requires macOS and Photos library access permissions
- Default: last 30 days, max 100 photos
- Photos sorted by date (newest first)
- Useful for quick access to recent screenshots, images
- Export preserves original filenames and metadata

**Related Services**:
- `ApplePhotosService`: macOS Photos library integration

---

## Data Models Reference

### Media
- **Media** (table): Image/file records with metadata
- Fields: id (UUID), original_media_id (file-XXX), storage_path, mime_type, file_size_bytes, original_filename, width, height, platform, extra_metadata (JSONB), collection_id, message_id, created_at

### Chunks
- **Chunk** (table): Text/image content segments
- Fields: id (UUID), message_id, collection_id, chunk_type (e.g., "image"), content (JSON string for images), chunk_sequence, embedding, created_at
- Image chunks use `content` field to store JSON with image_asset_pointer structure

### Transformation Jobs
- **TransformationJob** (table): Vision processing jobs
- Fields: id (UUID), job_type (vision_ocr, vision_describe, etc.), status (pending, in_progress, completed, failed), source_chunk_id, result_chunk_id, parameters (JSONB), result_data (JSONB), error_message, created_at, updated_at

### Image Metadata Structure

**Media.extra_metadata** (JSONB):
```json
{
  "uploaded_by": "user-123",
  "format": "PNG",
  "mode": "RGB",
  "exif": {
    "DateTimeOriginal": "2025:10:07 12:00:00",
    "Make": "Apple",
    "Model": "iPhone 14 Pro",
    "GPSLatitude": 37.7749,
    "GPSLongitude": -122.4194
  },
  "ai_metadata": {
    "prompt": "A serene mountain landscape at sunset",
    "generator": "DALL-E 3",
    "model": "dall-e-3",
    "steps": 50,
    "guidance_scale": 7.5
  },
  "created_date": "2025-10-07T12:00:00",
  "camera": "iPhone 14 Pro"
}
```

**Chunk content for images** (stored as JSON string):
```json
{
  "content_type": "image_asset_pointer",
  "asset_pointer": "file-service://file-a1b2c3d4e5f6g7h8i9j0k1l2",
  "size_bytes": 245678,
  "width": 1024,
  "height": 1024,
  "fovea": null,
  "metadata": {
    "original_filename": "image.png",
    "uploaded": true
  }
}
```

---

## Common Patterns

### AI Metadata Detection

The ImageMetadataExtractor service detects AI generation metadata from:

1. **DALL-E Images**:
   - Checks for `parameters.prompt` in PNG metadata
   - Extracts model info, prompt text

2. **Stable Diffusion Images**:
   - Checks for `parameters` field in PNG metadata
   - Extracts: prompt, negative_prompt, steps, cfg_scale, seed, model

3. **Midjourney Images**:
   - Checks EXIF UserComment for `/imagine prompt:` prefix
   - Extracts prompt text from comment

4. **Generic Metadata**:
   - EXIF data: camera, GPS, timestamps
   - Image properties: dimensions, format, mode

### File ID Format

All uploaded files use consistent file ID format:
- Pattern: `file-{24-char-hex}`
- Example: `file-a1b2c3d4e5f6g7h8i9j0k1l2`
- Generated using: `f"file-{uuid4().hex[:24]}"`
- Compatible with ChatGPT file ID format

### Storage Paths

- Upload directory: `backend/media/uploads/`
- Filename: `{file_id}.{ext}`
- Example: `backend/media/uploads/file-a1b2c3d4e5f6g7h8i9j0k1l2.png`
- Extensions: .png, .jpg, .webp, .gif

### Vision Job Types

Valid job types for vision processing:
- `vision_ocr`: Extract text from images (OCR)
- `vision_describe`: Generate detailed image descriptions
- `vision_analyze`: Analyze image content (objects, scene, composition)
- `vision_diagram`: Extract structured data from diagrams/charts

### Error Handling

Standard HTTP status codes:
- 200: Success
- 201: Created (successful upload/job creation)
- 400: Invalid request (bad file type, invalid job type, Photos unavailable)
- 404: Resource not found (media not found, job not found)
- 500: Server error (upload failed, OCR failed, Photos export failed)

---

## Integration Notes

### Frontend Integration

These endpoints support:
- **Image Upload**: Drag-drop upload with metadata display
- **Image Browser**: Display uploaded images with AI prompts
- **Vision Pipeline**: Create OCR/analysis jobs, poll for results
- **Apple Photos Integration**: Browse albums, export photos

### Background Processing

Vision jobs created via POST /jobs are processed by background worker:
1. Job created with status "pending"
2. Worker picks up job from queue
3. Worker calls Claude Vision API
4. Worker updates job status to "completed" or "failed"
5. Worker creates result chunk if successful
6. Frontend polls GET /jobs/{job_id} for status

### Claude Vision API

Direct OCR endpoint uses Claude Vision API synchronously:
- Model: claude-3-sonnet or claude-3-opus
- Input: Image file path + optional prompt
- Output: Extracted text with confidence score
- Rate limits apply (see Claude API docs)
- Requires valid ANTHROPIC_API_KEY

### Apple Photos Integration

macOS-specific functionality:
- Uses AppleScript or SQLite to access Photos library
- Requires Full Disk Access permission for Python
- Read-only access (does not modify Photos library)
- Exports are file copies (preserves originals)

---

## Performance Considerations

### Image Upload

- File size limits: Not enforced (consider adding max_file_size)
- Metadata extraction: Synchronous (may slow large uploads)
- Thumbnail generation: Not implemented (consider adding)
- Concurrent uploads: Supported (async endpoint)

### Bulk Upload

- Processes files sequentially (one at a time)
- Each file commits separately (allows partial success)
- Large batches may take significant time
- Consider adding progress callback for frontend

### Vision Jobs

- Async processing via background worker (recommended)
- Direct OCR blocks request (use sparingly)
- Claude API rate limits apply
- Job polling interval: 1-2 seconds recommended

### Apple Photos Export

- Large exports may take minutes (hundreds of photos)
- File copying is disk-intensive
- No progress callback (consider adding)
- Concurrent exports not recommended (filesystem contention)

---

## Security Considerations

### File Upload Validation

- File type whitelist enforced (PNG, JPEG, WEBP, GIF)
- No file size limit (consider adding: max 10MB)
- No filename sanitization (stored with UUID)
- No virus scanning (consider adding)

### File Storage

- Files stored in `backend/media/uploads/` only
- Filenames are UUIDs (prevents directory traversal)
- Storage path not user-controllable
- No cleanup mechanism (orphaned files may accumulate)

### Metadata Extraction

- PIL/Pillow used for metadata extraction
- EXIF data may contain sensitive info (GPS, camera)
- AI prompts may contain sensitive text
- Metadata stored in database (consider privacy implications)

### Apple Photos Access

- Requires Full Disk Access permission (macOS)
- Read-only access to Photos library
- No authentication/authorization (system-level only)
- Export paths user-controllable (validate/sanitize)

### Claude Vision API

- API key stored in environment variable
- API calls logged (may expose image content)
- Rate limits prevent abuse
- No image content filtering (consider adding)

---

## Dependencies

### Python Packages

- `fastapi`: Web framework
- `sqlalchemy`: ORM and async database
- `pydantic`: Data validation
- `PIL/Pillow`: Image metadata extraction
- `anthropic`: Claude API client
- `uuid`: UUID generation
- `pathlib`: File path handling
- `shutil`: File operations

### Services

- `VisionService`: Claude Vision API wrapper
- `ImageMetadataExtractor`: AI metadata detection
- `ApplePhotosService`: macOS Photos integration

### Models

- `models.chunk_models`: Media, Chunk, Message, Collection
- `models.pipeline_models`: TransformationJob

### External APIs

- Claude Vision API (Anthropic)
- Apple Photos library (macOS only)

---

## Testing Recommendations

### Unit Tests

1. File type validation logic
2. File ID generation (format, uniqueness)
3. Metadata extraction (DALL-E, Stable Diffusion, Midjourney)
4. EXIF data parsing
5. Chunk content JSON serialization
6. Job type validation
7. Apple Photos availability check

### Integration Tests

1. Single file upload (PNG, JPEG, WEBP, GIF)
2. Bulk upload (mixed success/failure)
3. Upload with collection/message linking
4. Vision job creation (all job types)
5. Job status polling (pending → completed)
6. Direct OCR operation
7. Apple Photos album listing (macOS only)
8. Apple Photos export (macOS only)

### E2E Tests

1. Upload image → View in browser → Create OCR job → Poll result
2. Bulk upload folder → Browse images → Filter by AI generator
3. Export Apple Photos album → Upload to humanizer
4. Upload image with AI prompt → Display metadata in UI

### Error Case Tests

1. Invalid file type (400 error)
2. Corrupted image file (500 error)
3. Invalid job type (400 error)
4. Non-existent media_id (404 error)
5. Apple Photos unavailable (400 error)
6. Invalid export path (500 error)
7. Claude API error (500 error)

### Performance Tests

1. Large file upload (10MB+ image)
2. Bulk upload (100+ files)
3. Concurrent uploads (10+ simultaneous)
4. Metadata extraction on large images
5. Apple Photos export (1000+ photos)

---

## Future Enhancements

1. **Thumbnail Generation** (TODO):
   - Generate thumbnails on upload for faster browsing
   - Store thumbnail paths in Media.extra_metadata
   - Serve via `/media/{media_id}/thumbnail` endpoint

2. **File Size Limits** (TODO):
   - Add max_file_size validation (e.g., 10MB)
   - Return 400 error with size info

3. **Cleanup Mechanism** (TODO):
   - Detect orphaned files in uploads directory
   - Add endpoint to delete unused media files
   - Implement retention policy

4. **Progress Callbacks** (TODO):
   - Add WebSocket for upload progress
   - Add progress tracking for bulk operations
   - Add progress for Apple Photos exports

5. **Image Processing** (TODO):
   - Add resize/crop operations
   - Add format conversion
   - Add watermarking

6. **Enhanced Metadata** (TODO):
   - Add face detection
   - Add object detection
   - Add color analysis
   - Add duplicate detection

7. **Vision Job Enhancements** (TODO):
   - Add batch processing for multiple images
   - Add retry mechanism for failed jobs
   - Add priority queue for jobs

8. **Apple Photos Enhancements** (TODO):
   - Add Smart Album support
   - Add photo metadata import (EXIF, GPS)
   - Add selective export (by date range, keywords)

---

## Changelog

- **Oct 2025**: Initial documentation created
- Vision system implemented with Claude API integration
- Apple Photos integration added (macOS only)
- AI metadata detection added (DALL-E, Stable Diffusion, Midjourney)
- Image upload and bulk upload endpoints implemented

---

**End of Documentation**
