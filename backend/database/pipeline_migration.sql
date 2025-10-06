-- ============================================================================
-- TRANSFORMATION PIPELINE MIGRATION
-- ============================================================================
--
-- Adds tables and indexes for batch transformation pipeline:
-- - transformation_jobs: Batch transformation jobs with progress tracking
-- - chunk_transformations: Links source chunks to transformed results
-- - transformation_lineage: Multi-generation transformation lineage
--
-- This migration is IDEMPOTENT - safe to run multiple times.
--
-- Author: Humanizer Agent
-- Date: 2025-10-05
-- ============================================================================

-- Enable required extensions (idempotent)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- TRANSFORMATION_JOBS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS transformation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,

    -- Identity
    name VARCHAR(500) NOT NULL,
    description TEXT,
    job_type VARCHAR(50) NOT NULL,

    -- Status and progress
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    progress_percentage FLOAT DEFAULT 0.0,
    current_item_id UUID,

    -- Error tracking
    error_message TEXT,
    error_count INTEGER DEFAULT 0,

    -- Configuration
    configuration JSONB NOT NULL DEFAULT '{}',

    -- Execution metadata
    tokens_used BIGINT DEFAULT 0,
    estimated_cost_usd FLOAT DEFAULT 0.0,
    processing_time_ms BIGINT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Priority
    priority INTEGER DEFAULT 0,

    -- Flexible metadata
    metadata JSONB NOT NULL DEFAULT '{}'
);

-- Indexes for transformation_jobs
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON transformation_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_session_id ON transformation_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON transformation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_status_user ON transformation_jobs(status, user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON transformation_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON transformation_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON transformation_jobs(priority DESC);

-- GIN index for configuration JSONB
CREATE INDEX IF NOT EXISTS idx_jobs_config_gin ON transformation_jobs USING GIN(configuration);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_transformation_job_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_transformation_job_updated_at ON transformation_jobs;
CREATE TRIGGER trigger_update_transformation_job_updated_at
    BEFORE UPDATE ON transformation_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_transformation_job_updated_at();

-- ============================================================================
-- CHUNK_TRANSFORMATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS chunk_transformations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Job reference
    job_id UUID NOT NULL REFERENCES transformation_jobs(id) ON DELETE CASCADE,

    -- Source and result
    source_chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    result_chunk_id UUID REFERENCES chunks(id) ON DELETE SET NULL,

    -- Link to old transformation system
    transformation_id UUID REFERENCES transformations(id) ON DELETE SET NULL,

    -- Transformation details
    transformation_type VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',

    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,

    -- Execution metadata
    tokens_used INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Sequence in job
    sequence_number INTEGER,

    -- Flexible metadata
    metadata JSONB NOT NULL DEFAULT '{}'
);

-- Indexes for chunk_transformations
CREATE INDEX IF NOT EXISTS idx_chunk_trans_job_id ON chunk_transformations(job_id);
CREATE INDEX IF NOT EXISTS idx_chunk_trans_source ON chunk_transformations(source_chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_trans_result ON chunk_transformations(result_chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_trans_transformation ON chunk_transformations(transformation_id);
CREATE INDEX IF NOT EXISTS idx_chunk_trans_type ON chunk_transformations(transformation_type);
CREATE INDEX IF NOT EXISTS idx_chunk_trans_status ON chunk_transformations(status);
CREATE INDEX IF NOT EXISTS idx_chunk_trans_sequence ON chunk_transformations(job_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_chunk_trans_created_at ON chunk_transformations(created_at DESC);

-- GIN index for parameters JSONB
CREATE INDEX IF NOT EXISTS idx_chunk_trans_params_gin ON chunk_transformations USING GIN(parameters);

-- ============================================================================
-- TRANSFORMATION_LINEAGE TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS transformation_lineage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Root and current chunk
    root_chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,

    -- Generation tracking
    generation INTEGER NOT NULL DEFAULT 0,
    transformation_path TEXT[] DEFAULT '{}',

    -- Parent in lineage
    parent_lineage_id UUID REFERENCES transformation_lineage(id) ON DELETE SET NULL,

    -- Session and job tracking
    session_ids UUID[] DEFAULT '{}',
    job_ids UUID[] DEFAULT '{}',

    -- Graph metadata
    depth INTEGER DEFAULT 0,
    branch_id UUID,

    -- Statistics
    total_transformations INTEGER DEFAULT 0,
    total_tokens_used BIGINT DEFAULT 0,

    -- Flexible metadata
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for transformation_lineage (optimized for graph queries)
CREATE INDEX IF NOT EXISTS idx_lineage_root ON transformation_lineage(root_chunk_id);
CREATE INDEX IF NOT EXISTS idx_lineage_chunk ON transformation_lineage(chunk_id);
CREATE INDEX IF NOT EXISTS idx_lineage_generation ON transformation_lineage(generation);
CREATE INDEX IF NOT EXISTS idx_lineage_parent ON transformation_lineage(parent_lineage_id);
CREATE INDEX IF NOT EXISTS idx_lineage_branch ON transformation_lineage(branch_id);
CREATE INDEX IF NOT EXISTS idx_lineage_depth ON transformation_lineage(depth);

-- GIN indexes for array columns
CREATE INDEX IF NOT EXISTS idx_lineage_sessions_gin ON transformation_lineage USING GIN(session_ids);
CREATE INDEX IF NOT EXISTS idx_lineage_jobs_gin ON transformation_lineage USING GIN(job_ids);
CREATE INDEX IF NOT EXISTS idx_lineage_path_gin ON transformation_lineage USING GIN(transformation_path);

-- Composite index for efficient lineage traversal
CREATE INDEX IF NOT EXISTS idx_lineage_root_generation ON transformation_lineage(root_chunk_id, generation);

-- Trigger to update updated_at
DROP TRIGGER IF EXISTS trigger_update_transformation_lineage_updated_at ON transformation_lineage;
CREATE TRIGGER trigger_update_transformation_lineage_updated_at
    BEFORE UPDATE ON transformation_lineage
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ENHANCED CHUNK_RELATIONSHIPS INDEXES
-- ============================================================================
-- Additional indexes for existing chunk_relationships table to support graph queries

CREATE INDEX IF NOT EXISTS idx_chunk_rel_source ON chunk_relationships(source_chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_rel_target ON chunk_relationships(target_chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_rel_type ON chunk_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_chunk_rel_type_source ON chunk_relationships(relationship_type, source_chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_rel_strength ON chunk_relationships(strength DESC);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Get transformation lineage tree
-- Returns all ancestors of a chunk in the transformation lineage
CREATE OR REPLACE FUNCTION get_transformation_lineage(
    p_chunk_id UUID
)
RETURNS TABLE (
    id UUID,
    root_chunk_id UUID,
    chunk_id UUID,
    generation INTEGER,
    transformation_path TEXT[],
    depth INTEGER,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE lineage_tree AS (
        -- Base case: start with the given chunk
        SELECT
            l.id,
            l.root_chunk_id,
            l.chunk_id,
            l.generation,
            l.transformation_path,
            l.depth,
            l.metadata,
            l.parent_lineage_id,
            0 AS traversal_depth
        FROM transformation_lineage l
        WHERE l.chunk_id = p_chunk_id

        UNION ALL

        -- Recursive case: get parent lineage
        SELECT
            l.id,
            l.root_chunk_id,
            l.chunk_id,
            l.generation,
            l.transformation_path,
            l.depth,
            l.metadata,
            l.parent_lineage_id,
            lt.traversal_depth + 1
        FROM transformation_lineage l
        INNER JOIN lineage_tree lt ON l.id = lt.parent_lineage_id
    )
    SELECT
        lt.id,
        lt.root_chunk_id,
        lt.chunk_id,
        lt.generation,
        lt.transformation_path,
        lt.depth,
        lt.metadata
    FROM lineage_tree lt
    ORDER BY lt.traversal_depth;
END;
$$ LANGUAGE plpgsql;

-- Function: Get transformation descendants
-- Returns all descendants of a chunk in the transformation lineage
CREATE OR REPLACE FUNCTION get_transformation_descendants(
    p_chunk_id UUID,
    p_max_depth INTEGER DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    chunk_id UUID,
    generation INTEGER,
    transformation_path TEXT[],
    depth INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE lineage_descendants AS (
        -- Base case: start with the given chunk
        SELECT
            l.id,
            l.chunk_id,
            l.generation,
            l.transformation_path,
            l.depth,
            0 AS traversal_depth
        FROM transformation_lineage l
        WHERE l.chunk_id = p_chunk_id

        UNION ALL

        -- Recursive case: get children
        SELECT
            l.id,
            l.chunk_id,
            l.generation,
            l.transformation_path,
            l.depth,
            ld.traversal_depth + 1
        FROM transformation_lineage l
        INNER JOIN lineage_descendants ld ON l.parent_lineage_id = ld.id
        WHERE p_max_depth IS NULL OR ld.traversal_depth < p_max_depth
    )
    SELECT
        ld.id,
        ld.chunk_id,
        ld.generation,
        ld.transformation_path,
        ld.depth
    FROM lineage_descendants ld
    ORDER BY ld.traversal_depth, ld.generation;
END;
$$ LANGUAGE plpgsql;

-- Function: Get chunk transformation graph
-- Returns transformation graph for visualization (nodes + edges)
CREATE OR REPLACE FUNCTION get_chunk_transformation_graph(
    p_root_chunk_id UUID
)
RETURNS TABLE (
    node_id UUID,
    node_content TEXT,
    node_generation INTEGER,
    edge_source UUID,
    edge_target UUID,
    edge_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS node_id,
        c.content AS node_content,
        l.generation AS node_generation,
        l.parent_lineage_id AS edge_source,
        l.id AS edge_target,
        CASE
            WHEN l.transformation_path IS NOT NULL AND array_length(l.transformation_path, 1) > 0
            THEN l.transformation_path[array_length(l.transformation_path, 1)]
            ELSE 'unknown'
        END AS edge_type
    FROM transformation_lineage l
    INNER JOIN chunks c ON l.chunk_id = c.id
    WHERE l.root_chunk_id = p_root_chunk_id
    ORDER BY l.generation, l.depth;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Job progress summary
CREATE OR REPLACE VIEW transformation_job_progress AS
SELECT
    j.id,
    j.name,
    j.job_type,
    j.status,
    j.total_items,
    j.processed_items,
    j.failed_items,
    CASE
        WHEN j.total_items > 0
        THEN ROUND((j.processed_items::FLOAT / j.total_items::FLOAT * 100)::NUMERIC, 2)
        ELSE 0
    END AS progress_percentage,
    j.tokens_used,
    j.estimated_cost_usd,
    EXTRACT(EPOCH FROM (COALESCE(j.completed_at, NOW()) - j.started_at)) AS elapsed_seconds,
    j.created_at,
    j.started_at,
    j.completed_at
FROM transformation_jobs j;

-- View: Transformation statistics per job
CREATE OR REPLACE VIEW transformation_job_stats AS
SELECT
    j.id AS job_id,
    j.name AS job_name,
    j.job_type,
    j.status,
    COUNT(ct.id) AS total_transformations,
    COUNT(ct.id) FILTER (WHERE ct.status = 'completed') AS completed_transformations,
    COUNT(ct.id) FILTER (WHERE ct.status = 'failed') AS failed_transformations,
    SUM(ct.tokens_used) AS total_tokens_used,
    AVG(ct.processing_time_ms) AS avg_processing_time_ms,
    MAX(ct.processing_time_ms) AS max_processing_time_ms
FROM transformation_jobs j
LEFT JOIN chunk_transformations ct ON j.id = ct.job_id
GROUP BY j.id, j.name, j.job_type, j.status;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE transformation_jobs IS 'Batch transformation jobs for processing multiple chunks';
COMMENT ON TABLE chunk_transformations IS 'Links source chunks to their transformed results';
COMMENT ON TABLE transformation_lineage IS 'Multi-generation transformation lineage for graph visualization';

COMMENT ON FUNCTION get_transformation_lineage(UUID) IS 'Get all ancestors of a chunk in transformation lineage';
COMMENT ON FUNCTION get_transformation_descendants(UUID, INTEGER) IS 'Get all descendants of a chunk in transformation lineage';
COMMENT ON FUNCTION get_chunk_transformation_graph(UUID) IS 'Get transformation graph for visualization (nodes + edges)';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE '✅ Transformation pipeline migration completed successfully!';
    RAISE NOTICE '   - Created tables: transformation_jobs, chunk_transformations, transformation_lineage';
    RAISE NOTICE '   - Created indexes for efficient graph queries';
    RAISE NOTICE '   - Created helper functions for lineage traversal';
    RAISE NOTICE '   - Created views for job progress monitoring';
END $$;
