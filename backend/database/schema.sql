-- PostgreSQL + pgvector schema for Humanizer Agent
-- Enables semantic search and session management

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    preferences JSONB DEFAULT '{}'::jsonb,
    -- Nullable for anonymous users
    is_anonymous BOOLEAN DEFAULT true
);

-- Sessions table - groups related transformations
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Metadata for session context
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Track total transformations in session
    transformation_count INTEGER DEFAULT 0,
    -- Session status
    is_archived BOOLEAN DEFAULT false
);

-- Transformations table with vector embeddings
CREATE TABLE transformations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Source content
    source_text TEXT NOT NULL,
    source_embedding vector(1536), -- OpenAI ada-002 or Claude embeddings

    -- Transformation parameters (Symbolic Realm)
    persona VARCHAR(100) NOT NULL,
    namespace VARCHAR(100) NOT NULL,
    style VARCHAR(100) NOT NULL,

    -- Transformed content
    transformed_content TEXT,
    transformed_embedding vector(1536),

    -- Philosophical metadata
    belief_framework JSONB,
    emotional_profile TEXT,
    philosophical_context TEXT,

    -- Execution metadata
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    error_message TEXT,
    tokens_used INTEGER,
    processing_time_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Relational tracking
    parent_transformation_id UUID REFERENCES transformations(id) ON DELETE SET NULL,
    is_checkpoint BOOLEAN DEFAULT false,

    -- Full metadata capture
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Belief patterns table - track recurring frameworks
CREATE TABLE belief_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Pattern identification
    pattern_name VARCHAR(200) NOT NULL,
    persona VARCHAR(100),
    namespace VARCHAR(100),
    style VARCHAR(100),

    -- Pattern analysis
    frequency_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Representative embedding (centroid of all instances)
    pattern_embedding vector(1536),

    -- Insights
    philosophical_insight TEXT,
    emotional_signature TEXT,

    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_transformations_session_id ON transformations(session_id);
CREATE INDEX idx_transformations_user_id ON transformations(user_id);
CREATE INDEX idx_transformations_status ON transformations(status);
CREATE INDEX idx_transformations_created_at ON transformations(created_at DESC);
CREATE INDEX idx_belief_patterns_user_id ON belief_patterns(user_id);

-- Vector similarity search indexes (HNSW for fast approximate nearest neighbor)
CREATE INDEX idx_transformations_source_embedding ON transformations
    USING hnsw (source_embedding vector_cosine_ops);
CREATE INDEX idx_transformations_transformed_embedding ON transformations
    USING hnsw (transformed_embedding vector_cosine_ops);
CREATE INDEX idx_belief_patterns_embedding ON belief_patterns
    USING hnsw (pattern_embedding vector_cosine_ops);

-- Trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to increment session transformation count
CREATE OR REPLACE FUNCTION increment_session_transformation_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions
    SET transformation_count = transformation_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER increment_transformation_count AFTER INSERT ON transformations
    FOR EACH ROW EXECUTE FUNCTION increment_session_transformation_count();

-- Helper function: Find similar transformations by source text
CREATE OR REPLACE FUNCTION find_similar_transformations(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.8,
    max_results integer DEFAULT 10
)
RETURNS TABLE (
    transformation_id UUID,
    similarity float,
    source_text TEXT,
    persona VARCHAR(100),
    namespace VARCHAR(100),
    style VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        1 - (t.source_embedding <=> query_embedding) as similarity,
        t.source_text,
        t.persona,
        t.namespace,
        t.style
    FROM transformations t
    WHERE t.source_embedding IS NOT NULL
        AND 1 - (t.source_embedding <=> query_embedding) >= similarity_threshold
    ORDER BY t.source_embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Helper function: Get session summary with stats
CREATE OR REPLACE FUNCTION get_session_summary(session_uuid UUID)
RETURNS TABLE (
    session_id UUID,
    title VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    transformation_count INTEGER,
    most_recent_transformation TIMESTAMP WITH TIME ZONE,
    unique_personas TEXT[],
    unique_namespaces TEXT[],
    total_tokens_used BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.title,
        s.description,
        s.created_at,
        s.updated_at,
        s.transformation_count,
        MAX(t.created_at) as most_recent,
        ARRAY_AGG(DISTINCT t.persona) as personas,
        ARRAY_AGG(DISTINCT t.namespace) as namespaces,
        SUM(t.tokens_used)::BIGINT as total_tokens
    FROM sessions s
    LEFT JOIN transformations t ON t.session_id = s.id
    WHERE s.id = session_uuid
    GROUP BY s.id, s.title, s.description, s.created_at, s.updated_at, s.transformation_count;
END;
$$ LANGUAGE plpgsql;
