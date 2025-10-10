"""Add artifacts system for persistent semantic outputs

Revision ID: 005_add_artifacts_system
Revises: 004_add_semantic_regions
Create Date: 2025-10-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '005_add_artifacts_system'
down_revision = '72ef3f47d0a5'
branch_labels = None
depends_on = None


def upgrade():
    # Artifacts table - stores all generated semantic outputs
    op.create_table(
        'artifacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),

        # Classification
        sa.Column('artifact_type', sa.String(50), nullable=False),
        sa.Column('operation', sa.String(100), nullable=False),

        # Content
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_format', sa.String(20), server_default='markdown'),
        sa.Column('content_embedding', Vector(1024), nullable=True),

        # Provenance (what created this)
        sa.Column('source_chunk_ids', ARRAY(UUID(as_uuid=True)), nullable=True),
        sa.Column('source_artifact_ids', ARRAY(UUID(as_uuid=True)), nullable=True),
        sa.Column('source_operation_params', JSONB, nullable=True),

        # Lineage (iterative refinement)
        sa.Column('parent_artifact_id', UUID(as_uuid=True), sa.ForeignKey('artifacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('lineage_depth', sa.Integer, server_default='0'),

        # Quality metadata
        sa.Column('token_count', sa.Integer, nullable=True),
        sa.Column('generation_model', sa.String(100), nullable=True),
        sa.Column('generation_prompt', sa.Text, nullable=True),

        # Semantic metadata
        sa.Column('topics', ARRAY(sa.Text), nullable=True),
        sa.Column('frameworks', ARRAY(sa.Text), nullable=True),
        sa.Column('sentiment', sa.Float, nullable=True),
        sa.Column('complexity_score', sa.Float, nullable=True),

        # User interaction
        sa.Column('is_approved', sa.Boolean, server_default='false'),
        sa.Column('user_rating', sa.Integer, nullable=True),
        sa.Column('user_notes', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),

        # Flexible metadata
        sa.Column('custom_metadata', JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    # Indexes for performance
    op.create_index('idx_artifacts_user', 'artifacts', ['user_id'])
    op.create_index('idx_artifacts_type', 'artifacts', ['artifact_type'])
    op.create_index('idx_artifacts_operation', 'artifacts', ['operation'])
    op.create_index('idx_artifacts_parent', 'artifacts', ['parent_artifact_id'])
    op.create_index('idx_artifacts_created', 'artifacts', ['created_at'], postgresql_ops={'created_at': 'DESC'})

    # Semantic search index (IVFFlat for fast approximate search)
    op.execute(
        'CREATE INDEX idx_artifacts_embedding ON artifacts '
        'USING ivfflat (content_embedding vector_cosine_ops) '
        'WITH (lists = 100)'
    )

    # Source tracking (GIN for array containment queries)
    op.create_index(
        'idx_artifacts_source_chunks',
        'artifacts',
        ['source_chunk_ids'],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_artifacts_source_artifacts',
        'artifacts',
        ['source_artifact_ids'],
        postgresql_using='gin'
    )

    # JSONB metadata search
    op.create_index(
        'idx_artifacts_metadata',
        'artifacts',
        ['custom_metadata'],
        postgresql_using='gin'
    )

    # Topics array search
    op.create_index(
        'idx_artifacts_topics',
        'artifacts',
        ['topics'],
        postgresql_using='gin'
    )


def downgrade():
    op.drop_index('idx_artifacts_topics', table_name='artifacts')
    op.drop_index('idx_artifacts_metadata', table_name='artifacts')
    op.drop_index('idx_artifacts_source_artifacts', table_name='artifacts')
    op.drop_index('idx_artifacts_source_chunks', table_name='artifacts')
    op.drop_index('idx_artifacts_embedding', table_name='artifacts')
    op.drop_index('idx_artifacts_created', table_name='artifacts')
    op.drop_index('idx_artifacts_parent', table_name='artifacts')
    op.drop_index('idx_artifacts_operation', table_name='artifacts')
    op.drop_index('idx_artifacts_type', table_name='artifacts')
    op.drop_index('idx_artifacts_user', table_name='artifacts')
    op.drop_table('artifacts')
