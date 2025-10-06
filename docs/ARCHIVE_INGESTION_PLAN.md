# Archive & File Ingestion System

## Overview

Support for ingesting historical transformations, documents, and archives into the belief framework analysis system.

## File Types to Support

### 1. Text Documents
- `.txt` - Plain text files
- `.md` - Markdown documents
- `.pdf` - PDF documents (text extraction)
- `.docx` - Word documents

### 2. Archives
- `.zip` - ZIP archives containing multiple files
- `.tar.gz` - Compressed archives
- Bulk transformation histories

### 3. Structured Data
- `.json` - Transformation history exports
- `.csv` - Tabular data with text columns
- `.jsonl` - JSON Lines (streaming format)

## Database Schema Extensions

### New Table: Documents

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,

    -- File metadata
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT,
    original_path TEXT,

    -- Content
    raw_content TEXT,
    content_embedding vector(1536),

    -- Processing
    status VARCHAR(50) DEFAULT 'pending',
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Analysis
    detected_language VARCHAR(10),
    word_count INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_session_id ON documents(session_id);
CREATE INDEX idx_documents_content_embedding ON documents
    USING hnsw (content_embedding vector_cosine_ops);
```

### New Table: Archive Jobs

```sql
CREATE TABLE archive_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,

    -- Job details
    job_type VARCHAR(50) NOT NULL, -- 'file_upload', 'bulk_import', 'archive_extract'
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Results
    result_summary JSONB,
    error_log TEXT[],

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    metadata JSONB DEFAULT '{}'::jsonb
);
```

## API Endpoints

### File Upload

```python
@router.post("/api/documents/upload")
async def upload_document(
    file: UploadFile,
    session_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a single document.

    - Extracts text content
    - Generates embeddings
    - Optionally runs transformation
    """
```

### Archive Processing

```python
@router.post("/api/archives/process")
async def process_archive(
    file: UploadFile,
    session_id: str,
    user_id: str,
    auto_transform: bool = False,
    belief_framework: Optional[BeliefFramework] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Process an archive of documents.

    - Extracts all files
    - Processes each document
    - Creates transformations if requested
    - Updates archive_jobs table
    """
```

### Bulk Import

```python
@router.post("/api/import/bulk")
async def bulk_import(
    data: List[ImportRecord],
    session_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk import transformation records.

    Useful for:
    - Migration from other systems
    - Importing historical data
    - Batch processing results
    """
```

### Archive Analysis

```python
@router.post("/api/archives/analyze")
async def analyze_archive(
    session_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze all documents/transformations in a session.

    Returns:
    - Belief pattern distribution
    - Temporal evolution
    - Semantic clusters
    - Network graph data
    """
```

## Processing Pipeline

### Stage 1: File Extraction

```python
async def extract_text(file_path: str, file_type: str) -> str:
    """Extract text from various file formats."""

    if file_type == '.pdf':
        return extract_pdf_text(file_path)
    elif file_type == '.docx':
        return extract_docx_text(file_path)
    elif file_type == '.txt' or file_type == '.md':
        return read_text_file(file_path)
    elif file_type == '.zip':
        return extract_archive(file_path)
```

### Stage 2: Content Analysis

```python
async def analyze_content(content: str, db: AsyncSession):
    """Analyze extracted content."""

    # Generate embedding
    embedding = await embedding_service.generate_embedding(content)

    # Detect language
    language = detect_language(content)

    # Count words
    word_count = len(content.split())

    # Extract potential belief frameworks
    frameworks = detect_belief_frameworks(content)

    return {
        'embedding': embedding,
        'language': language,
        'word_count': word_count,
        'frameworks': frameworks
    }
```

### Stage 3: Transformation (Optional)

```python
async def transform_document(
    document_id: UUID,
    belief_framework: BeliefFramework,
    db: AsyncSession
):
    """Transform imported document using belief framework."""

    # Get document
    document = await db.get(Document, document_id)

    # Create transformation
    transformation = Transformation(
        session_id=document.session_id,
        user_id=document.user_id,
        source_text=document.raw_content,
        persona=belief_framework.persona,
        namespace=belief_framework.namespace,
        style=belief_framework.style,
        # ... transformation logic
    )

    db.add(transformation)
    await db.commit()
```

## Frontend Components

### File Upload Component

```jsx
<DocumentUploader
  sessionId={currentSession.id}
  userId={userId}
  onUploadComplete={(doc) => {
    // Refresh documents list
    // Optionally trigger transformation
  }}
  acceptedTypes={['.txt', '.md', '.pdf', '.docx', '.zip']}
/>
```

### Archive Browser

```jsx
<ArchiveBrowser
  sessionId={currentSession.id}
  documents={documents}
  onSelectDocument={(doc) => {
    // Load document
    // Show transformation options
  }}
  onAnalyze={() => {
    // Run archive analysis
    // Show belief pattern network
  }}
/>
```

### Batch Transformation

```jsx
<BatchTransformationPanel
  documents={selectedDocuments}
  beliefFramework={framework}
  onStartBatch={async (docs, framework) => {
    // Create archive job
    // Process each document
    // Update progress
  }}
/>
```

## Use Cases

### 1. Personal Writing Archive
- Upload all your writing (essays, journals, emails)
- Analyze belief evolution over time
- Identify recurring frameworks
- Visualize consciousness patterns

### 2. Research Corpus Analysis
- Import academic papers
- Transform through multiple frameworks
- Compare interpretations
- Generate semantic network

### 3. Historical Document Study
- Upload historical texts
- Apply modern belief frameworks
- Reveal constructed meanings
- Comparative analysis

### 4. Migration from Other Systems
- Export data from other tools
- Bulk import via JSON/CSV
- Preserve transformation history
- Maintain belief pattern continuity

## Implementation Priorities

### Phase 1: Basic File Upload ✓ (Partially exists)
- [x] File upload endpoint
- [ ] Text extraction (PDF, DOCX)
- [ ] Document storage in DB
- [ ] Embedding generation

### Phase 2: Archive Processing
- [ ] ZIP/archive extraction
- [ ] Batch document processing
- [ ] Archive jobs tracking
- [ ] Progress reporting

### Phase 3: Analysis & Visualization
- [ ] Belief pattern detection across documents
- [ ] Temporal evolution analysis
- [ ] Semantic clustering
- [ ] Network graph generation

### Phase 4: Advanced Features
- [ ] Real-time processing
- [ ] Streaming large files
- [ ] Distributed processing
- [ ] Vector similarity search UI

## Vector Search Applications

Once documents are ingested with embeddings:

```sql
-- Find documents similar to current text
SELECT d.*,
       1 - (d.content_embedding <=> query_embedding) as similarity
FROM documents d
WHERE 1 - (d.content_embedding <=> query_embedding) > 0.8
ORDER BY d.content_embedding <=> query_embedding
LIMIT 10;

-- Find transformations of similar content
SELECT t.*,
       1 - (t.source_embedding <=> document_embedding) as similarity
FROM transformations t
WHERE 1 - (t.source_embedding <=> document_embedding) > 0.8
ORDER BY similarity DESC;

-- Cluster documents by semantic similarity
-- (Use k-means or HDBSCAN on embeddings)
```

## Security Considerations

1. **File Size Limits**: Max 100MB per file, 1GB per archive
2. **Type Validation**: Strict file type checking
3. **Virus Scanning**: Scan uploaded files
4. **Rate Limiting**: Max 10 uploads per minute
5. **Storage Quotas**: Per-user storage limits
6. **Access Control**: Users can only access their documents

## Next Steps

1. Create `documents` and `archive_jobs` tables
2. Implement file extraction utilities
3. Build upload API endpoints
4. Create frontend upload component
5. Add batch processing queue
6. Implement archive analysis

Would you like me to start implementing any of these components?
