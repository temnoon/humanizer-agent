-- ============================================================================
-- Humanizer Agent: Chunk-Based Database Schema
-- ============================================================================
--
-- This schema implements a chunk-based architecture for storing and searching
-- all content types: AI conversations, transformations, social media, documents.
--
-- Core Concepts:
-- 1. Collections: Top-level containers (conversations, sessions, archives)
-- 2. Messages: Individual messages within collections (with role, sequence)
-- 3. Chunks: All text chunks at any granularity with progressive summarization
-- 4. Chunk Relationships: Non-linear connections (transformations, citations)
-- 5. Media: Images, audio, video with OCR/transcription → chunks
-- 6. Belief Frameworks: Structured tracking of persona/namespace/style
--
-- Key Features:
-- - Progressive summarization: base chunks → section summaries → message summary
-- - Hierarchical navigation: chunk → message → collection
-- - Variable-grain chunking: ~320 tokens typical, 1 sentence to 1024 tokens
-- - Vector search at any chunk level
-- - Media archival: remove blobs, keep metadata + embeddings
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. COLLECTIONS TABLE
-- ============================================================================
-- Top-level containers: conversations, sessions, documents, archives
-- Links to all messages and media within the collection

CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Identity
    title TEXT NOT NULL,
    description TEXT,
    collection_type TEXT NOT NULL,  -- 'conversation', 'session', 'document', 'archive'

    -- Origin tracking
    source_platform TEXT,  -- 'chatgpt', 'claude', 'humanizer', 'twitter', 'facebook', 'custom'
    source_format TEXT,    -- 'chatgpt_json', 'claude_project', 'twitter_api', 'manual'
    original_id TEXT,      -- Platform-specific ID (e.g., ChatGPT conversation ID)
    import_date TIMESTAMP WITH TIME ZONE,

    -- Statistics (updated by triggers)
    message_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    media_count INTEGER DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,

    -- Flexible metadata (JSONB for any additional fields)
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Example: {"chatgpt_model": "gpt-4", "conversation_mode": "browsing"}

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Archival
    is_archived BOOLEAN DEFAULT false,

    -- Constraints
    CONSTRAINT valid_collection_type CHECK (
        collection_type IN ('conversation', 'session', 'document', 'archive', 'custom')
    )
);

-- Indexes for collections
CREATE INDEX idx_collections_user_id ON collections(user_id);
CREATE INDEX idx_collections_type ON collections(collection_type);
CREATE INDEX idx_collections_source ON collections(source_platform);
CREATE INDEX idx_collections_created ON collections(created_at DESC);
CREATE INDEX idx_collections_archived ON collections(is_archived);
CREATE INDEX idx_collections_original_id ON collections(original_id) WHERE original_id IS NOT NULL;

-- Full-text search on collections
CREATE INDEX idx_collections_title_fts ON collections USING gin(to_tsvector('english', title));
CREATE INDEX idx_collections_description_fts ON collections USING gin(to_tsvector('english', description));

COMMENT ON TABLE collections IS 'Top-level containers for messages, chunks, and media';
COMMENT ON COLUMN collections.collection_type IS 'Type of collection: conversation (AI chat), session (transformation session), document, archive';
COMMENT ON COLUMN collections.source_platform IS 'Origin platform: chatgpt, claude, humanizer, twitter, facebook, custom';
COMMENT ON COLUMN collections.original_id IS 'Platform-specific identifier for traceability';


-- ============================================================================
-- 2. MESSAGES TABLE
-- ============================================================================
-- Individual messages within collections
-- Supports conversation structure (system, user, assistant, tool)
-- Each message has ONE summary chunk + many base chunks

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Message hierarchy (for nested messages: tool calls inside assistant)
    parent_message_id UUID REFERENCES messages(id) ON DELETE CASCADE,

    -- Position in conversation
    sequence_number INTEGER NOT NULL,  -- Order within collection (0-indexed)

    -- Message identity
    role TEXT NOT NULL,  -- 'system', 'user', 'assistant', 'tool'
    message_type TEXT,   -- 'transformation', 'contemplation', 'socratic', 'standard', 'tool_call'

    -- Summary chunk (the ONE chunk that summarizes entire message)
    -- Set after progressive summarization completes
    summary_chunk_id UUID,  -- References chunks(id)

    -- Origin tracking
    original_message_id TEXT,  -- Platform-specific message ID
    timestamp TIMESTAMP WITH TIME ZONE,  -- Original message timestamp

    -- Statistics (updated by triggers)
    chunk_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    media_count INTEGER DEFAULT 0,

    -- Flexible metadata (JSONB for belief frameworks, tool calls, etc.)
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Examples:
    -- Transformation: {"persona": "Scholar", "namespace": "quantum-physics", "style": "formal", "depth": 0.7}
    -- Tool call: {"tool_call": {"name": "web_search", "arguments": {"query": "..."}}}
    -- Tool result: {"is_tool_result": true, "tool_call_id": "call_abc123"}
    -- Contemplation: {"exercise_type": "word_dissolution", "target_word": "success"}

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_role CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    CONSTRAINT valid_message_type CHECK (
        message_type IN ('transformation', 'contemplation', 'socratic', 'witness', 'standard', 'tool_call', NULL)
    ),
    CONSTRAINT unique_sequence_per_collection UNIQUE (collection_id, sequence_number)
);

-- Indexes for messages
CREATE INDEX idx_messages_collection_id ON messages(collection_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_parent ON messages(parent_message_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_sequence ON messages(collection_id, sequence_number);
CREATE INDEX idx_messages_summary_chunk ON messages(summary_chunk_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);

-- GIN index for metadata search
CREATE INDEX idx_messages_metadata ON messages USING gin(metadata);

COMMENT ON TABLE messages IS 'Individual messages within collections with conversation structure';
COMMENT ON COLUMN messages.role IS 'Message role in conversation: system, user, assistant, tool';
COMMENT ON COLUMN messages.parent_message_id IS 'Parent message for nested structure (e.g., tool calls inside assistant message)';
COMMENT ON COLUMN messages.summary_chunk_id IS 'The ONE chunk that summarizes this entire message';
COMMENT ON COLUMN messages.sequence_number IS 'Order within collection, 0-indexed';


-- ============================================================================
-- 3. CHUNKS TABLE
-- ============================================================================
-- All text chunks at any granularity level
-- Supports hierarchical structure: document → paragraph → sentence
-- Includes progressive summarization: base chunks → section summaries → message summary

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE NOT NULL,
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Content
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'text',  -- 'text', 'code', 'markdown', 'html', 'latex'
    token_count INTEGER,

    -- Embedding
    embedding vector(1024),  -- Supports mxbai-embed-large (1024) or nomic-embed-text (768)
    embedding_model TEXT,    -- Track which model generated this: 'mxbai-embed-large', 'nomic-embed-text', 'openai-ada-002'
    embedding_generated_at TIMESTAMP WITH TIME ZONE,

    -- Hierarchical structure (Document → Paragraph → Sentence)
    parent_chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE,
    chunk_level TEXT NOT NULL,  -- 'document', 'paragraph', 'sentence'
    chunk_sequence INTEGER NOT NULL,  -- Order within parent (or within message if no parent)

    -- Progressive summarization
    is_summary BOOLEAN DEFAULT false,
    summary_type TEXT,  -- NULL for base chunks, 'section_summary', 'message_summary'
    summarizes_chunk_ids UUID[],  -- Array of chunk IDs this summary represents
    summarization_prompt TEXT,  -- Prompt used to generate this summary

    -- Position in original message (for exact reconstruction)
    char_start INTEGER,  -- Character offset in original message
    char_end INTEGER,    -- Character offset end

    -- Flexible metadata (JSONB for all use cases)
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Examples:
    -- Import: {"origin": "chatgpt_import", "role": "assistant", "chatgpt_message_id": "msg_123"}
    -- Transformation: {"transformation_type": "multi_perspective", "persona": "Poet", "source_chunk_id": "chunk_abc"}
    -- Contemplation: {"exercise_type": "word_dissolution", "target_word": "success", "emotional_weight": "high"}
    -- OCR: {"ocr_source_media_id": "media_abc123", "confidence": 0.95, "ocr_engine": "tesseract"}
    -- Transcription: {"transcription_source_media_id": "media_xyz789", "audio_duration": 45.3}

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_chunk_level CHECK (chunk_level IN ('document', 'paragraph', 'sentence')),
    CONSTRAINT valid_content_type CHECK (
        content_type IN ('text', 'code', 'markdown', 'html', 'latex', 'json', 'xml')
    ),
    CONSTRAINT valid_summary_type CHECK (
        summary_type IN ('section_summary', 'message_summary', NULL)
    ),
    CONSTRAINT summary_has_type CHECK (
        (is_summary = false AND summary_type IS NULL) OR
        (is_summary = true AND summary_type IS NOT NULL)
    )
);

-- Indexes for chunks
CREATE INDEX idx_chunks_message_id ON chunks(message_id);
CREATE INDEX idx_chunks_collection_id ON chunks(collection_id);
CREATE INDEX idx_chunks_user_id ON chunks(user_id);
CREATE INDEX idx_chunks_parent ON chunks(parent_chunk_id);
CREATE INDEX idx_chunks_level ON chunks(chunk_level);
CREATE INDEX idx_chunks_is_summary ON chunks(is_summary);
CREATE INDEX idx_chunks_summary_type ON chunks(summary_type) WHERE summary_type IS NOT NULL;
CREATE INDEX idx_chunks_embedding_model ON chunks(embedding_model);
CREATE INDEX idx_chunks_created ON chunks(created_at DESC);

-- Vector similarity search index (HNSW for fast approximate nearest neighbor)
CREATE INDEX idx_chunks_embedding ON chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Full-text search on chunk content
CREATE INDEX idx_chunks_content_fts ON chunks USING gin(to_tsvector('english', content));

-- GIN index for metadata search
CREATE INDEX idx_chunks_metadata ON chunks USING gin(metadata);

COMMENT ON TABLE chunks IS 'All text chunks at any granularity with hierarchical structure and progressive summarization';
COMMENT ON COLUMN chunks.chunk_level IS 'Granularity: document (whole message), paragraph, sentence';
COMMENT ON COLUMN chunks.is_summary IS 'True if this chunk summarizes other chunks';
COMMENT ON COLUMN chunks.summarizes_chunk_ids IS 'Array of chunk IDs this summary represents';
COMMENT ON COLUMN chunks.embedding IS 'Vector embedding for semantic search (1024 or 768 dimensions)';


-- ============================================================================
-- 4. CHUNK RELATIONSHIPS TABLE
-- ============================================================================
-- Non-linear connections between chunks
-- Enables: transformations, citations, replies, contradictions, support

CREATE TABLE IF NOT EXISTS chunk_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE NOT NULL,
    target_chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE NOT NULL,

    relationship_type TEXT NOT NULL,
    -- Relationship types:
    -- 'transforms_into' - transformation relationship (source → transformed)
    -- 'cites' - citation/quote relationship
    -- 'responds_to' - conversational reply
    -- 'continues' - continuation/split
    -- 'summarizes' - summary relationship (alternative to summarizes_chunk_ids)
    -- 'contradicts' - philosophical opposition
    -- 'supports' - philosophical agreement
    -- 'references' - general reference
    -- 'derived_from' - derived content (OCR, transcription)

    -- Relationship metadata (JSONB for flexibility)
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Examples:
    -- Transformation: {"belief_framework": {"persona": "Scholar", "namespace": "quantum-physics", "style": "formal"}}
    -- Citation: {"citation_type": "direct_quote", "char_range": "120-450"}
    -- Similarity: {"similarity_score": 0.87}
    -- OCR: {"ocr_confidence": 0.95, "ocr_engine": "tesseract"}

    -- Relationship strength (optional, for weighted graphs)
    strength FLOAT DEFAULT 1.0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_relationship_type CHECK (
        relationship_type IN (
            'transforms_into', 'cites', 'responds_to', 'continues',
            'summarizes', 'contradicts', 'supports', 'references', 'derived_from'
        )
    ),
    CONSTRAINT no_self_reference CHECK (source_chunk_id != target_chunk_id),
    CONSTRAINT valid_strength CHECK (strength >= 0.0 AND strength <= 1.0)
);

-- Indexes for chunk relationships
CREATE INDEX idx_relationships_source ON chunk_relationships(source_chunk_id);
CREATE INDEX idx_relationships_target ON chunk_relationships(target_chunk_id);
CREATE INDEX idx_relationships_type ON chunk_relationships(relationship_type);
CREATE INDEX idx_relationships_created ON chunk_relationships(created_at DESC);

-- GIN index for metadata search
CREATE INDEX idx_relationships_metadata ON chunk_relationships USING gin(metadata);

-- Ensure no duplicate relationships (same source, target, type)
CREATE UNIQUE INDEX idx_relationships_unique ON chunk_relationships(
    source_chunk_id, target_chunk_id, relationship_type
);

COMMENT ON TABLE chunk_relationships IS 'Non-linear connections between chunks for transformations, citations, replies, etc.';
COMMENT ON COLUMN chunk_relationships.relationship_type IS 'Type of relationship: transforms_into, cites, responds_to, etc.';
COMMENT ON COLUMN chunk_relationships.strength IS 'Relationship strength (0.0 to 1.0) for weighted graphs';


-- ============================================================================
-- 5. MEDIA TABLE
-- ============================================================================
-- Images, audio, video, documents
-- Links to collections and messages
-- Supports archival (remove blob, keep metadata + embeddings)
-- OCR and transcription create chunks

CREATE TABLE IF NOT EXISTS media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE NOT NULL,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,  -- Message-level link (optional)
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Media identity
    media_type TEXT NOT NULL,  -- 'image', 'audio', 'video', 'document'
    mime_type TEXT,
    original_filename TEXT,

    -- Storage
    is_archived BOOLEAN DEFAULT false,
    storage_path TEXT,  -- Local file path or URL (for archived media)
    blob_data BYTEA,    -- Actual media blob (NULL if archived)
    size_bytes BIGINT,

    -- Archive metadata (populated when is_archived = true)
    archive_metadata JSONB,
    -- Example: {"archived_at": "2025-10-05T12:00:00Z", "reason": "user_request", "original_hash": "sha256:abc123..."}

    -- Media embeddings (CLIP for images, audio embeddings for audio)
    embedding vector(1024),  -- Image/audio embeddings
    embedding_model TEXT,    -- 'clip-vit-base-patch32', 'whisper-embed', etc.
    embedding_generated_at TIMESTAMP WITH TIME ZONE,

    -- Processed text (OCR from images, transcription from audio)
    extracted_text TEXT,
    extraction_method TEXT,  -- 'ocr_tesseract', 'ocr_claude', 'whisper_transcription', 'manual'
    extraction_confidence FLOAT,  -- Confidence score (0.0 to 1.0)

    -- Linked chunks (OCR/transcription creates chunks, store IDs here)
    generated_chunk_ids UUID[],  -- Array of chunk IDs created from this media

    -- Origin tracking
    original_media_id TEXT,  -- Platform-specific media ID (e.g., ChatGPT file-abc123)

    -- Media dimensions and properties
    width INTEGER,
    height INTEGER,
    duration_seconds FLOAT,  -- For audio/video

    -- Flexible metadata (JSONB for format-specific fields)
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Examples:
    -- ChatGPT: {"chatgpt_file_id": "file-abc123", "chatgpt_download_url": "..."}
    -- Generated audio: {"generated_audio": true, "voice": "alloy", "tts_model": "gpt-4-audio"}
    -- User audio: {"user_audio": true, "input_device": "microphone", "sample_rate": 44100}
    -- Image: {"camera_model": "iPhone 12", "gps_location": {"lat": 37.7749, "lng": -122.4194}}

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_media_type CHECK (media_type IN ('image', 'audio', 'video', 'document')),
    CONSTRAINT valid_extraction_confidence CHECK (
        extraction_confidence IS NULL OR (extraction_confidence >= 0.0 AND extraction_confidence <= 1.0)
    ),
    CONSTRAINT archived_no_blob CHECK (
        (is_archived = false) OR (is_archived = true AND blob_data IS NULL)
    )
);

-- Indexes for media
CREATE INDEX idx_media_collection_id ON media(collection_id);
CREATE INDEX idx_media_message_id ON media(message_id);
CREATE INDEX idx_media_user_id ON media(user_id);
CREATE INDEX idx_media_type ON media(media_type);
CREATE INDEX idx_media_archived ON media(is_archived);
CREATE INDEX idx_media_original_id ON media(original_media_id) WHERE original_media_id IS NOT NULL;
CREATE INDEX idx_media_extraction_method ON media(extraction_method) WHERE extraction_method IS NOT NULL;

-- Vector search for images/audio
CREATE INDEX idx_media_embedding ON media
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Full-text search on extracted text
CREATE INDEX idx_media_extracted_text_fts ON media
    USING gin(to_tsvector('english', extracted_text))
    WHERE extracted_text IS NOT NULL;

-- GIN index for metadata search
CREATE INDEX idx_media_metadata ON media USING gin(metadata);

COMMENT ON TABLE media IS 'Images, audio, video, documents with OCR/transcription and archival support';
COMMENT ON COLUMN media.is_archived IS 'If true, blob_data is NULL but metadata + embeddings preserved';
COMMENT ON COLUMN media.generated_chunk_ids IS 'Array of chunk IDs created from OCR/transcription of this media';
COMMENT ON COLUMN media.extraction_confidence IS 'Confidence score (0.0-1.0) for OCR/transcription quality';


-- ============================================================================
-- 6. BELIEF FRAMEWORKS TABLE
-- ============================================================================
-- Structured tracking of persona/namespace/style combinations
-- Tracks usage patterns and representative embeddings

CREATE TABLE IF NOT EXISTS belief_frameworks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Framework identity
    framework_name TEXT,  -- Optional friendly name (e.g., "Quantum Scholar")
    persona TEXT NOT NULL,
    namespace TEXT NOT NULL,
    style TEXT NOT NULL,

    -- Framework definition
    emotional_profile TEXT,
    philosophical_context TEXT,
    framework_definition JSONB,  -- Full structured definition
    -- Example: {"core_values": ["precision", "wonder"], "communication_style": {"formality": 0.8, "creativity": 0.6}}

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    first_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Representative embedding (centroid of all transformations using this framework)
    representative_embedding vector(1024),
    embedding_model TEXT,

    -- Flexible metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_framework_per_user UNIQUE (user_id, persona, namespace, style)
);

-- Indexes for belief frameworks
CREATE INDEX idx_frameworks_user_id ON belief_frameworks(user_id);
CREATE INDEX idx_frameworks_persona ON belief_frameworks(persona);
CREATE INDEX idx_frameworks_namespace ON belief_frameworks(namespace);
CREATE INDEX idx_frameworks_style ON belief_frameworks(style);
CREATE INDEX idx_frameworks_usage ON belief_frameworks(usage_count DESC);

-- Vector search for similar frameworks
CREATE INDEX idx_frameworks_embedding ON belief_frameworks
    USING hnsw (representative_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- GIN index for metadata and framework definition
CREATE INDEX idx_frameworks_metadata ON belief_frameworks USING gin(metadata);
CREATE INDEX idx_frameworks_definition ON belief_frameworks USING gin(framework_definition);

COMMENT ON TABLE belief_frameworks IS 'Structured tracking of persona/namespace/style combinations with usage patterns';
COMMENT ON COLUMN belief_frameworks.representative_embedding IS 'Centroid embedding of all transformations using this framework';
COMMENT ON COLUMN belief_frameworks.usage_count IS 'Number of times this framework has been used';


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update updated_at timestamp on row update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chunks_updated_at BEFORE UPDATE ON chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_media_updated_at BEFORE UPDATE ON media
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_frameworks_updated_at BEFORE UPDATE ON belief_frameworks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Increment collection counts when messages are added
CREATE OR REPLACE FUNCTION increment_collection_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE collections
    SET message_count = message_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.collection_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER increment_message_count AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION increment_collection_message_count();

-- Increment message chunk count when chunks are added
CREATE OR REPLACE FUNCTION increment_message_chunk_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE messages
    SET chunk_count = chunk_count + 1,
        token_count = token_count + COALESCE(NEW.token_count, 0),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.message_id;

    -- Also increment collection chunk count and total tokens
    UPDATE collections
    SET chunk_count = chunk_count + 1,
        total_tokens = total_tokens + COALESCE(NEW.token_count, 0),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.collection_id;

    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER increment_chunk_count AFTER INSERT ON chunks
    FOR EACH ROW EXECUTE FUNCTION increment_message_chunk_count();

-- Increment collection media count when media is added
CREATE OR REPLACE FUNCTION increment_collection_media_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE collections
    SET media_count = media_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.collection_id;

    -- Also increment message media count if message_id is set
    IF NEW.message_id IS NOT NULL THEN
        UPDATE messages
        SET media_count = media_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.message_id;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER increment_media_count AFTER INSERT ON media
    FOR EACH ROW EXECUTE FUNCTION increment_collection_media_count();


-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Find similar chunks by embedding (semantic search)
CREATE OR REPLACE FUNCTION find_similar_chunks(
    query_embedding vector(1024),
    similarity_threshold float DEFAULT 0.7,
    max_results integer DEFAULT 20,
    filter_user_id UUID DEFAULT NULL,
    filter_collection_ids UUID[] DEFAULT NULL,
    filter_chunk_level TEXT DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    similarity float,
    content TEXT,
    chunk_level TEXT,
    message_id UUID,
    collection_id UUID,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        1 - (c.embedding <=> query_embedding) as similarity,
        c.content,
        c.chunk_level,
        c.message_id,
        c.collection_id,
        c.metadata
    FROM chunks c
    WHERE c.embedding IS NOT NULL
        AND 1 - (c.embedding <=> query_embedding) >= similarity_threshold
        AND (filter_user_id IS NULL OR c.user_id = filter_user_id)
        AND (filter_collection_ids IS NULL OR c.collection_id = ANY(filter_collection_ids))
        AND (filter_chunk_level IS NULL OR c.chunk_level = filter_chunk_level)
    ORDER BY c.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_similar_chunks IS 'Semantic search for similar chunks using vector embeddings';


-- Get full message hierarchy (summary → section summaries → base chunks)
CREATE OR REPLACE FUNCTION get_message_chunk_hierarchy(message_uuid UUID)
RETURNS TABLE (
    chunk_id UUID,
    content TEXT,
    chunk_level TEXT,
    is_summary BOOLEAN,
    summary_type TEXT,
    parent_chunk_id UUID,
    chunk_sequence INTEGER,
    depth INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE chunk_tree AS (
        -- Start with message summary
        SELECT
            c.id,
            c.content,
            c.chunk_level,
            c.is_summary,
            c.summary_type,
            c.parent_chunk_id,
            c.chunk_sequence,
            0 as depth
        FROM chunks c
        WHERE c.id = (SELECT summary_chunk_id FROM messages WHERE id = message_uuid)

        UNION ALL

        -- Recursively get child chunks
        SELECT
            c.id,
            c.content,
            c.chunk_level,
            c.is_summary,
            c.summary_type,
            c.parent_chunk_id,
            c.chunk_sequence,
            ct.depth + 1
        FROM chunks c
        JOIN chunk_tree ct ON c.parent_chunk_id = ct.chunk_id
    )
    SELECT * FROM chunk_tree ORDER BY depth, chunk_sequence;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_message_chunk_hierarchy IS 'Get hierarchical structure of chunks for a message';


-- Get collection summary with statistics
CREATE OR REPLACE FUNCTION get_collection_summary(collection_uuid UUID)
RETURNS TABLE (
    collection_id UUID,
    title TEXT,
    description TEXT,
    collection_type TEXT,
    source_platform TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER,
    chunk_count INTEGER,
    media_count INTEGER,
    total_tokens BIGINT,
    most_recent_message TIMESTAMP WITH TIME ZONE,
    unique_roles TEXT[],
    unique_personas TEXT[],
    unique_namespaces TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.title,
        c.description,
        c.collection_type,
        c.source_platform,
        c.created_at,
        c.updated_at,
        c.message_count,
        c.chunk_count,
        c.media_count,
        c.total_tokens,
        MAX(m.timestamp) as most_recent,
        ARRAY_AGG(DISTINCT m.role) FILTER (WHERE m.role IS NOT NULL) as roles,
        ARRAY_AGG(DISTINCT m.metadata->>'persona') FILTER (WHERE m.metadata->>'persona' IS NOT NULL) as personas,
        ARRAY_AGG(DISTINCT m.metadata->>'namespace') FILTER (WHERE m.metadata->>'namespace' IS NOT NULL) as namespaces
    FROM collections c
    LEFT JOIN messages m ON m.collection_id = c.id
    WHERE c.id = collection_uuid
    GROUP BY c.id, c.title, c.description, c.collection_type, c.source_platform,
             c.created_at, c.updated_at, c.message_count, c.chunk_count, c.media_count, c.total_tokens;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_collection_summary IS 'Get comprehensive summary and statistics for a collection';


-- Archive media (remove blob, keep metadata + embeddings)
CREATE OR REPLACE FUNCTION archive_media(media_uuid UUID, archive_reason TEXT DEFAULT 'user_request')
RETURNS BOOLEAN AS $$
DECLARE
    media_hash TEXT;
    media_size BIGINT;
BEGIN
    -- Get blob hash and size before deletion
    SELECT
        encode(digest(blob_data, 'sha256'), 'hex'),
        octet_length(blob_data)
    INTO media_hash, media_size
    FROM media
    WHERE id = media_uuid AND is_archived = false;

    -- Update media record
    UPDATE media
    SET
        is_archived = true,
        blob_data = NULL,
        archive_metadata = jsonb_build_object(
            'archived_at', CURRENT_TIMESTAMP,
            'reason', archive_reason,
            'original_hash', media_hash,
            'original_size_bytes', media_size
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = media_uuid;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION archive_media IS 'Archive media by removing blob but keeping metadata and embeddings';


-- Find related chunks via relationships
CREATE OR REPLACE FUNCTION get_related_chunks(
    chunk_uuid UUID,
    relationship_types TEXT[] DEFAULT NULL,
    max_depth INTEGER DEFAULT 1
)
RETURNS TABLE (
    chunk_id UUID,
    content TEXT,
    relationship_type TEXT,
    relationship_metadata JSONB,
    depth INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE related AS (
        -- Direct relationships
        SELECT
            cr.target_chunk_id as chunk_id,
            cr.relationship_type,
            cr.metadata as relationship_metadata,
            1 as depth
        FROM chunk_relationships cr
        WHERE cr.source_chunk_id = chunk_uuid
            AND (relationship_types IS NULL OR cr.relationship_type = ANY(relationship_types))

        UNION

        -- Recursive relationships (up to max_depth)
        SELECT
            cr.target_chunk_id,
            cr.relationship_type,
            cr.metadata,
            r.depth + 1
        FROM chunk_relationships cr
        JOIN related r ON cr.source_chunk_id = r.chunk_id
        WHERE r.depth < max_depth
            AND (relationship_types IS NULL OR cr.relationship_type = ANY(relationship_types))
    )
    SELECT
        r.chunk_id,
        c.content,
        r.relationship_type,
        r.relationship_metadata,
        r.depth
    FROM related r
    JOIN chunks c ON c.id = r.chunk_id
    ORDER BY r.depth, r.relationship_type;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_related_chunks IS 'Get chunks related via relationships, with optional type filtering and depth limit';


-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Collections with enriched statistics
CREATE OR REPLACE VIEW collections_enriched AS
SELECT
    c.*,
    COUNT(DISTINCT m.id) as actual_message_count,
    COUNT(DISTINCT ch.id) as actual_chunk_count,
    COUNT(DISTINCT me.id) as actual_media_count,
    SUM(ch.token_count) as actual_total_tokens,
    MAX(m.timestamp) as most_recent_message_timestamp,
    MIN(m.timestamp) as oldest_message_timestamp
FROM collections c
LEFT JOIN messages m ON m.collection_id = c.id
LEFT JOIN chunks ch ON ch.collection_id = c.id
LEFT JOIN media me ON me.collection_id = c.id
GROUP BY c.id;

COMMENT ON VIEW collections_enriched IS 'Collections with actual counts (for validation against cached counts)';


-- View: Message summaries only
CREATE OR REPLACE VIEW message_summaries AS
SELECT
    m.id as message_id,
    m.collection_id,
    m.role,
    m.sequence_number,
    m.timestamp,
    c.id as summary_chunk_id,
    c.content as summary_content,
    c.token_count as summary_token_count,
    m.metadata as message_metadata
FROM messages m
LEFT JOIN chunks c ON c.id = m.summary_chunk_id
ORDER BY m.collection_id, m.sequence_number;

COMMENT ON VIEW message_summaries IS 'Messages with their summary chunks (one chunk per message)';


-- ============================================================================
-- PERMISSIONS (Adjust based on your application's user model)
-- ============================================================================

-- Example: Grant access to application role
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO humanizer_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO humanizer_app;

-- ============================================================================
-- COMPLETION
-- ============================================================================

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Chunk-based schema created successfully!';
    RAISE NOTICE 'Tables: collections, messages, chunks, chunk_relationships, media, belief_frameworks';
    RAISE NOTICE 'Helper functions: find_similar_chunks, get_message_chunk_hierarchy, get_collection_summary, archive_media, get_related_chunks';
    RAISE NOTICE 'Views: collections_enriched, message_summaries';
END $$;
