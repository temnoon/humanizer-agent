# Vision System Architecture
## Image Upload + Claude Vision OCR

**Created**: October 5, 2025
**Status**: In Development

---

## Overview

The Vision System enables users to:
1. Upload images (notebooks, screenshots, diagrams)
2. Use Claude's vision API for OCR and analysis
3. Transform handwritten notes → markdown
4. Integrate with Book Builder for publication

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                  Image Upload Flow                      │
│                                                         │
│  User Upload → Backend Storage → Media DB Record        │
│  (Drag/Drop)   (media/ folder)   (with metadata)       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Claude Vision Processing                    │
│                                                         │
│  1. vision_ocr: Handwriting → Markdown                  │
│  2. vision_describe: Image → Caption                    │
│  3. vision_analyze: Q&A about image                     │
│  4. vision_diagram: Diagram → Text description          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│               Transformation Pipeline                    │
│                                                         │
│  - Background job processing                            │
│  - Store results as new chunks                          │
│  - Link original image → OCR text                       │
│  - Provenance tracking                                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                Book Integration                         │
│                                                         │
│  - Add image + OCR to book sections                     │
│  - Side-by-side view in editor                          │
│  - Edit transcriptions                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Existing Tables (No Changes Needed)

**media**:
```sql
- id: UUID
- original_media_id: VARCHAR (file-XXX format)
- storage_path: TEXT (path to file)
- mime_type: VARCHAR
- file_size_bytes: INTEGER
- width, height: INTEGER (for images)
- created_at: TIMESTAMP
```

**transformation_jobs**:
```sql
- id: UUID
- job_type: VARCHAR (vision_ocr, vision_describe, etc.)
- status: VARCHAR (pending, running, completed, failed)
- source_chunk_id: UUID (links to image chunk)
- result_chunk_id: UUID (links to OCR text)
- created_at: TIMESTAMP
```

**chunks**:
```sql
- id: UUID
- content: TEXT (markdown OCR result or image pointer JSON)
- chunk_type: VARCHAR (text, image, code)
```

### New Vision Job Types

Add to `TransformationJobType` enum:
- `vision_ocr`: Extract text from image (handwriting, printed)
- `vision_describe`: Generate detailed description
- `vision_analyze`: Answer questions about image
- `vision_diagram`: Extract structure from diagrams

---

## Backend Implementation

### 1. Vision Service (`backend/services/vision_service.py`)

```python
class VisionService:
    def __init__(self, anthropic_client):
        self.client = anthropic_client

    async def ocr_image(self, image_path: str, prompt: str = None) -> str:
        """
        Perform OCR on image using Claude vision.

        Args:
            image_path: Path to image file
            prompt: Optional custom prompt (default: transcribe)

        Returns:
            Markdown-formatted transcription
        """
        # Read image, encode to base64
        # Call Claude with vision message
        # Return markdown text

    async def describe_image(self, image_path: str) -> str:
        """Generate detailed description of image."""

    async def analyze_image(self, image_path: str, question: str) -> str:
        """Answer question about image."""

    async def extract_diagram(self, image_path: str) -> str:
        """Extract structure from diagram/flowchart."""
```

### 2. Vision Endpoints (`backend/api/vision_routes.py`)

```python
@router.post("/upload")
async def upload_image(
    file: UploadFile,
    collection_id: Optional[str] = None,
    user_id: str = Query(...)
):
    """
    Upload an image and create media + chunk records.

    Returns:
        {
            "media_id": "...",
            "chunk_id": "...",
            "storage_path": "...",
            "thumbnail_url": "/api/media/..."
        }
    """

@router.post("/ocr")
async def create_ocr_job(
    media_id: str,
    prompt: Optional[str] = None,
    add_to_collection: bool = True
):
    """
    Create OCR transformation job for an image.

    Returns:
        {
            "job_id": "...",
            "status": "pending",
            "media_id": "..."
        }
    """

@router.get("/jobs/{job_id}")
async def get_vision_job(job_id: str):
    """Get status and result of vision job."""
```

### 3. Job Processor Integration

Add vision job handlers to `backend/services/job_processor.py`:

```python
async def process_vision_ocr(job):
    """Process OCR job."""
    # Get source image from media table
    # Call vision_service.ocr_image()
    # Create result chunk with markdown
    # Update job status

async def process_vision_describe(job):
    """Process description job."""

async def process_vision_analyze(job):
    """Process Q&A job."""
```

---

## Frontend Implementation

### 1. ImageUploader Component

**Location**: `frontend/src/components/ImageUploader.jsx`

**Features**:
- Drag-and-drop zone
- Multiple file selection
- Upload progress
- Preview thumbnails
- Bulk operations

```jsx
<ImageUploader
  onUpload={(files) => handleUploadComplete(files)}
  maxFiles={50}
  acceptedTypes={['image/png', 'image/jpeg']}
/>
```

### 2. VisionPanel Component

**Location**: `frontend/src/components/panels/VisionPanel.jsx`

**Features**:
- Image preview
- OCR button
- Job progress tracking
- Result preview (side-by-side)
- Edit transcription
- "Add to Book" button

```jsx
<VisionPanel
  imageId={selectedImage.id}
  onOCRComplete={(result) => handleResult(result)}
/>
```

### 3. ImageGallery Component

**Location**: `frontend/src/components/ImageGallery.jsx`

**Features**:
- Grid view of uploaded images
- Filter by collection
- Batch OCR
- Select multiple images
- Delete/organize

---

## API Flow

### Upload Image

```http
POST /api/vision/upload
Content-Type: multipart/form-data

{
  "file": <binary>,
  "user_id": "...",
  "collection_id": "..." (optional)
}

Response:
{
  "media_id": "file-abc123",
  "chunk_id": "uuid",
  "storage_path": "media/chatgpt/file-abc123.png",
  "width": 1536,
  "height": 2048,
  "thumbnail_url": "/api/library/media/file-abc123"
}
```

### Request OCR

```http
POST /api/vision/ocr
Content-Type: application/json

{
  "media_id": "file-abc123",
  "prompt": "Transcribe this handwritten note to markdown. Preserve formatting.",
  "add_to_collection": true
}

Response:
{
  "job_id": "uuid",
  "status": "pending",
  "media_id": "file-abc123",
  "estimated_time": "10-30 seconds"
}
```

### Check Job Status

```http
GET /api/vision/jobs/{job_id}

Response:
{
  "id": "uuid",
  "status": "completed",
  "job_type": "vision_ocr",
  "source_chunk_id": "uuid",
  "result_chunk_id": "uuid",
  "result": {
    "content": "# My Handwritten Note\n\nThis is the transcription...",
    "confidence": "high",
    "processing_time": 15.3
  }
}
```

---

## Claude Vision API Integration

### Message Format

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64_encoded_image
                    }
                },
                {
                    "type": "text",
                    "text": "Transcribe this handwritten note to markdown..."
                }
            ]
        }
    ]
)
```

### Prompts

**OCR (Handwriting)**:
```
Transcribe this handwritten note to markdown.

Requirements:
- Preserve original formatting (headings, lists, paragraphs)
- Use markdown syntax for structure
- If text is unclear, use [unclear: best guess] notation
- Preserve any diagrams as ASCII art or descriptions
- Include page numbers if visible

Return only the transcribed content as markdown.
```

**OCR (Printed Text)**:
```
Extract all text from this image as markdown.
Preserve document structure (headings, lists, tables).
```

**Describe**:
```
Provide a detailed description of this image.
Include:
- Main subject/content
- Visual style and composition
- Notable details
- Text if present
- Overall purpose/context
```

**Analyze**:
```
{user_question}

Analyze the image and answer the question.
Be specific and reference visual details.
```

---

## Use Cases

### 1. Digitize Handwritten Notebook

```
1. Upload 50 photos of notebook pages
2. Batch OCR all pages
3. Review results (image + transcription side-by-side)
4. Edit any errors
5. Add all pages to book as chapters
6. Export to PDF
```

### 2. Extract Diagrams

```
1. Upload whiteboard photo
2. Use vision_diagram transformation
3. Get text description of diagram
4. Add to documentation
```

### 3. Archive Screenshots

```
1. Upload chat screenshots
2. OCR to extract conversations
3. Store as searchable text
4. Link to original images
```

---

## Performance Considerations

- **API Latency**: Claude vision ~5-15 seconds per image
- **Batch Processing**: Process jobs in background, don't block UI
- **Caching**: Store OCR results, don't re-process
- **Cost**: ~$0.01-0.05 per image (depending on tokens)
- **Rate Limits**: Respect Anthropic API limits

---

## Future Enhancements

### Phase 2: Advanced Features
- **Batch OCR**: Process entire folders
- **Quality detection**: Auto-rotate, enhance contrast
- **Multi-page PDFs**: Extract as individual images
- **OCR correction**: AI-assisted editing

### Phase 3: Generation
- **DALL-E integration**: Text → image
- **Cover generator**: Auto-create book covers
- **Diagram generator**: Description → visual

---

## Testing Plan

1. **Unit tests**: Vision service functions
2. **Integration tests**: Upload → OCR → result
3. **Manual tests**: Real notebook images
4. **Quality tests**: Handwriting accuracy
5. **Performance tests**: Batch processing

---

## Status: In Development

- [x] Architecture design
- [ ] Backend vision service
- [ ] Vision API endpoints
- [ ] Job processor integration
- [ ] Frontend image uploader
- [ ] Vision panel UI
- [ ] OCR workflow
- [ ] Book integration
- [ ] Testing
- [ ] Documentation

**Next**: Implement backend vision service
