"""
Library API Response Models

Pydantic schemas for library browsing endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel


class CollectionSummary(BaseModel):
    """Summary of a collection for library browsing."""
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
    original_date: Optional[str]  # From metadata.create_time or import_date
    import_date: Optional[str]
    metadata: dict


class MessageSummary(BaseModel):
    """Summary of a message for library browsing."""
    id: str
    collection_id: str
    sequence_number: int
    role: str
    message_type: Optional[str]
    summary: Optional[str]  # First 200 chars of content
    chunk_count: int
    token_count: int
    media_count: int
    timestamp: Optional[str]
    created_at: str
    metadata: dict


class ChunkDetail(BaseModel):
    """Detailed chunk information."""
    id: str
    message_id: str
    content: str
    chunk_level: str
    chunk_sequence: int
    token_count: Optional[int]
    is_summary: bool
    has_embedding: bool
    created_at: str


class MediaDetail(BaseModel):
    """Media file information."""
    id: str
    collection_id: str
    message_id: Optional[str]
    media_type: str
    mime_type: Optional[str]
    original_filename: Optional[str]
    size_bytes: Optional[int]
    is_archived: bool
    storage_path: Optional[str]


class TransformationSummary(BaseModel):
    """Summary of a transformation job for library browsing."""
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
    source_message_id: Optional[str]  # Extracted from configuration
    source_collection_id: Optional[str]  # Extracted from configuration


class TransformationDetail(BaseModel):
    """Detailed view of a transformation job with source and results."""
    job: TransformationSummary
    source_message: Optional[MessageSummary]
    source_collection: Optional[CollectionSummary]
    transformations: List[dict]  # ChunkTransformation details
    lineage: List[dict]  # Lineage information


class CollectionHierarchy(BaseModel):
    """Full hierarchical view of a collection."""
    collection: CollectionSummary
    messages: List[MessageSummary]
    recent_chunks: List[ChunkDetail]  # Sample chunks
    media: List[MediaDetail]
