"""Add books system for paper/book building

Revision ID: 002_add_books_system
Revises: 001_baseline
Create Date: 2025-10-05 20:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '002_add_books_system'
down_revision = None  # First migration
branch_labels = None
depends_on = None


def upgrade():
    # Books table - top level container for papers/books
    op.create_table(
        'books',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('subtitle', sa.Text, nullable=True),
        sa.Column('book_type', sa.String(50), nullable=False, server_default='paper'),
        sa.Column('configuration', JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('metadata', JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    # Book sections - hierarchical chapters/sections
    op.create_table(
        'book_sections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('book_id', UUID(as_uuid=True), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_section_id', UUID(as_uuid=True), sa.ForeignKey('book_sections.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('section_type', sa.String(50), nullable=True),
        sa.Column('sequence_number', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('metadata', JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    # Book content links - link chunks/transformations to sections
    op.create_table(
        'book_content_links',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('section_id', UUID(as_uuid=True), sa.ForeignKey('book_sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', UUID(as_uuid=True), sa.ForeignKey('chunks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('transformation_job_id', UUID(as_uuid=True), sa.ForeignKey('transformation_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sequence_number', sa.Integer, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('idx_books_user_id', 'books', ['user_id'])
    op.create_index('idx_books_created_at', 'books', ['created_at'])
    op.create_index('idx_book_sections_book_id', 'book_sections', ['book_id'])
    op.create_index('idx_book_sections_parent_id', 'book_sections', ['parent_section_id'])
    op.create_index('idx_book_sections_sequence', 'book_sections', ['book_id', 'sequence_number'])
    op.create_index('idx_book_content_links_section_id', 'book_content_links', ['section_id'])
    op.create_index('idx_book_content_links_chunk_id', 'book_content_links', ['chunk_id'])
    op.create_index('idx_book_content_links_job_id', 'book_content_links', ['transformation_job_id'])


def downgrade():
    op.drop_table('book_content_links')
    op.drop_table('book_sections')
    op.drop_table('books')
