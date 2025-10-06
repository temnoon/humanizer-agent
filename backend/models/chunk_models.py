"""
SQLAlchemy models for chunk-based architecture.

This module defines the ORM models for the new chunk-based database schema,
which supports:
- Progressive summarization (base chunks → section summaries → message summaries)
- Multi-level embeddings for semantic search
- Flexible content types (conversations, transformations, social media, documents)
- Media with OCR/transcription
- Belief framework tracking
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, ForeignKey,
    DateTime, Float, BigInteger, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import Base and User from db_models to ensure proper relationships
from models.db_models import Base, User


# ============================================================================
# COLLECTION MODEL
# ============================================================================

class Collection(Base):
    """
    Top-level container for messages, chunks, and media.

    Examples:
    - AI conversation (ChatGPT, Claude)
    - Transformation session (Humanizer)
    - Social media archive (Twitter thread, Facebook posts)
    - Document collection
    """

    __tablename__ = "collections"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Identity
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    collection_type = Column(String(50), nullable=False)  # 'conversation', 'session', 'document', 'archive'

    # Origin tracking
    source_platform = Column(String(50), nullable=True)  # 'chatgpt', 'claude', 'humanizer', 'twitter', 'facebook'
    source_format = Column(String(50), nullable=True)    # 'chatgpt_json', 'claude_project', 'twitter_api'
    original_id = Column(String(200), nullable=True)     # Platform-specific ID
    import_date = Column(DateTime(timezone=True), nullable=True)

    # Statistics (updated by triggers)
    message_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    media_count = Column(Integer, default=0)
    total_tokens = Column(BigInteger, default=0)

    # Flexible metadata (using extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Archival
    is_archived = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", backref="collections")
    messages = relationship("Message", back_populates="collection", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="collection", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="collection", cascade="all, delete-orphan")

    def to_dict(self, include_messages: bool = False, include_stats: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "collection_type": self.collection_type,
            "source_platform": self.source_platform,
            "source_format": self.source_format,
            "original_id": self.original_id,
            "import_date": self.import_date.isoformat() if self.import_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_archived": self.is_archived,
            "metadata": self.extra_metadata or {}
        }

        if include_stats:
            result.update({
                "message_count": self.message_count,
                "chunk_count": self.chunk_count,
                "media_count": self.media_count,
                "total_tokens": self.total_tokens
            })

        if include_messages:
            result["messages"] = [m.to_dict() for m in self.messages]

        return result


# ============================================================================
# MESSAGE MODEL
# ============================================================================

class Message(Base):
    """
    Individual message within a collection.

    Supports:
    - Conversation structure (system, user, assistant, tool)
    - Nested messages (tool calls inside assistant messages)
    - One summary chunk per message
    """

    __tablename__ = "messages"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Hierarchy
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True)

    # Position
    sequence_number = Column(Integer, nullable=False)

    # Identity
    role = Column(String(20), nullable=False)  # 'system', 'user', 'assistant', 'tool'
    message_type = Column(String(50), nullable=True)  # 'transformation', 'contemplation', 'socratic', 'standard'

    # Summary
    summary_chunk_id = Column(UUID(as_uuid=True), nullable=True)  # References chunks.id

    # Origin tracking
    original_message_id = Column(String(200), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=True)

    # Statistics (updated by triggers)
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    media_count = Column(Integer, default=0)

    # Flexible metadata (using extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    collection = relationship("Collection", back_populates="messages")
    user = relationship("User", backref="messages")
    parent = relationship("Message", remote_side=[id], backref="children")
    chunks = relationship("Chunk", back_populates="message", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="message")

    def to_dict(self, include_chunks: bool = False, include_summary_only: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "collection_id": str(self.collection_id),
            "user_id": str(self.user_id),
            "parent_message_id": str(self.parent_message_id) if self.parent_message_id else None,
            "sequence_number": self.sequence_number,
            "role": self.role,
            "message_type": self.message_type,
            "summary_chunk_id": str(self.summary_chunk_id) if self.summary_chunk_id else None,
            "original_message_id": self.original_message_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "chunk_count": self.chunk_count,
            "token_count": self.token_count,
            "media_count": self.media_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.extra_metadata or {}
        }

        if include_summary_only and self.summary_chunk_id:
            # Include just the summary chunk
            summary_chunk = next((c for c in self.chunks if c.id == self.summary_chunk_id), None)
            if summary_chunk:
                result["summary"] = summary_chunk.to_dict()

        if include_chunks:
            result["chunks"] = [c.to_dict() for c in self.chunks]

        return result


# ============================================================================
# CHUNK MODEL
# ============================================================================

class Chunk(Base):
    """
    Text chunk at any granularity level.

    Supports:
    - Hierarchical structure (document → paragraph → sentence)
    - Progressive summarization (base chunks → section summaries → message summary)
    - Vector embeddings for semantic search
    """

    __tablename__ = "chunks"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Content
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default='text')
    token_count = Column(Integer, nullable=True)

    # Embedding
    embedding = Column(Vector(1024), nullable=True)  # Supports 1024 (mxbai) or 768 (nomic)
    embedding_model = Column(String(50), nullable=True)
    embedding_generated_at = Column(DateTime(timezone=True), nullable=True)

    # Hierarchy
    parent_chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=True)
    chunk_level = Column(String(20), nullable=False)  # 'document', 'paragraph', 'sentence'
    chunk_sequence = Column(Integer, nullable=False)

    # Summarization
    is_summary = Column(Boolean, default=False)
    summary_type = Column(String(30), nullable=True)  # 'section_summary', 'message_summary'
    summarizes_chunk_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    summarization_prompt = Column(Text, nullable=True)

    # Position in original message
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)

    # Flexible metadata (using extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    message = relationship("Message", back_populates="chunks")
    collection = relationship("Collection", back_populates="chunks")
    user = relationship("User", backref="chunks")
    parent = relationship("Chunk", remote_side=[id], backref="children")

    # Relationships via chunk_relationships table
    source_relationships = relationship(
        "ChunkRelationship",
        foreign_keys="ChunkRelationship.source_chunk_id",
        back_populates="source_chunk",
        cascade="all, delete-orphan"
    )
    target_relationships = relationship(
        "ChunkRelationship",
        foreign_keys="ChunkRelationship.target_chunk_id",
        back_populates="target_chunk",
        cascade="all, delete-orphan"
    )

    def to_dict(self, include_embedding: bool = False, include_children: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "collection_id": str(self.collection_id),
            "user_id": str(self.user_id),
            "content": self.content,
            "content_type": self.content_type,
            "token_count": self.token_count,
            "embedding_model": self.embedding_model,
            "embedding_generated_at": self.embedding_generated_at.isoformat() if self.embedding_generated_at else None,
            "parent_chunk_id": str(self.parent_chunk_id) if self.parent_chunk_id else None,
            "chunk_level": self.chunk_level,
            "chunk_sequence": self.chunk_sequence,
            "is_summary": self.is_summary,
            "summary_type": self.summary_type,
            "summarizes_chunk_ids": [str(cid) for cid in self.summarizes_chunk_ids] if self.summarizes_chunk_ids else None,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.extra_metadata or {}
        }

        if include_embedding and self.embedding is not None:
            result["embedding"] = self.embedding

        if include_children and self.children:
            result["children"] = [c.to_dict() for c in self.children]

        return result


# ============================================================================
# CHUNK RELATIONSHIP MODEL
# ============================================================================

class ChunkRelationship(Base):
    """
    Non-linear connections between chunks.

    Examples:
    - 'transforms_into': transformation relationship
    - 'cites': citation/quote
    - 'responds_to': conversational reply
    - 'contradicts': philosophical opposition
    - 'supports': philosophical agreement
    """

    __tablename__ = "chunk_relationships"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    source_chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)
    target_chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)

    relationship_type = Column(String(50), nullable=False)

    # Flexible metadata (using extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')

    # Relationship strength (0.0 to 1.0)
    strength = Column(Float, default=1.0)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source_chunk = relationship("Chunk", foreign_keys=[source_chunk_id], back_populates="source_relationships")
    target_chunk = relationship("Chunk", foreign_keys=[target_chunk_id], back_populates="target_relationships")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "source_chunk_id": str(self.source_chunk_id),
            "target_chunk_id": str(self.target_chunk_id),
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.extra_metadata or {}
        }


# ============================================================================
# MEDIA MODEL
# ============================================================================

class Media(Base):
    """
    Media associated with collections and messages.

    Supports:
    - Images, audio, video, documents
    - OCR and transcription → chunks
    - Archival (remove blob, keep metadata + embeddings)
    """

    __tablename__ = "media"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Media identity
    media_type = Column(String(20), nullable=False)  # 'image', 'audio', 'video', 'document'
    mime_type = Column(String(100), nullable=True)
    original_filename = Column(Text, nullable=True)

    # Storage
    is_archived = Column(Boolean, default=False)
    storage_path = Column(Text, nullable=True)
    blob_data = Column(BYTEA, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)

    # Archive metadata
    archive_metadata = Column(JSONB, nullable=True)

    # Media embeddings
    embedding = Column(Vector(1024), nullable=True)
    embedding_model = Column(String(50), nullable=True)
    embedding_generated_at = Column(DateTime(timezone=True), nullable=True)

    # Processed text (OCR, transcription)
    extracted_text = Column(Text, nullable=True)
    extraction_method = Column(String(50), nullable=True)
    extraction_confidence = Column(Float, nullable=True)

    # Linked chunks (created from OCR/transcription)
    generated_chunk_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)

    # Origin tracking
    original_media_id = Column(String(200), nullable=True)

    # Dimensions
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Flexible metadata (using extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    collection = relationship("Collection", back_populates="media")
    message = relationship("Message", back_populates="media")
    user = relationship("User", backref="media")

    def to_dict(self, include_blob: bool = False, include_embedding: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "collection_id": str(self.collection_id),
            "message_id": str(self.message_id) if self.message_id else None,
            "user_id": str(self.user_id),
            "media_type": self.media_type,
            "mime_type": self.mime_type,
            "original_filename": self.original_filename,
            "is_archived": self.is_archived,
            "storage_path": self.storage_path,
            "size_bytes": self.size_bytes,
            "archive_metadata": self.archive_metadata,
            "embedding_model": self.embedding_model,
            "embedding_generated_at": self.embedding_generated_at.isoformat() if self.embedding_generated_at else None,
            "extracted_text": self.extracted_text,
            "extraction_method": self.extraction_method,
            "extraction_confidence": self.extraction_confidence,
            "generated_chunk_ids": [str(cid) for cid in self.generated_chunk_ids] if self.generated_chunk_ids else None,
            "original_media_id": self.original_media_id,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.extra_metadata or {}
        }

        if include_blob and self.blob_data:
            result["blob_data"] = self.blob_data

        if include_embedding and self.embedding is not None:
            result["embedding"] = self.embedding

        return result


# ============================================================================
# BELIEF FRAMEWORK MODEL
# ============================================================================

class BeliefFramework(Base):
    """
    Structured tracking of persona/namespace/style combinations.

    Tracks usage patterns and representative embeddings for framework discovery.
    """

    __tablename__ = "belief_frameworks"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Framework identity
    framework_name = Column(String(200), nullable=True)
    persona = Column(String(100), nullable=False)
    namespace = Column(String(100), nullable=False)
    style = Column(String(100), nullable=False)

    # Framework definition
    emotional_profile = Column(Text, nullable=True)
    philosophical_context = Column(Text, nullable=True)
    framework_definition = Column(JSONB, nullable=True)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    first_used = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now())

    # Representative embedding (centroid)
    representative_embedding = Column(Vector(1024), nullable=True)
    embedding_model = Column(String(50), nullable=True)

    # Flexible metadata (using extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="belief_frameworks")

    def to_dict(self, include_embedding: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "framework_name": self.framework_name,
            "persona": self.persona,
            "namespace": self.namespace,
            "style": self.style,
            "emotional_profile": self.emotional_profile,
            "philosophical_context": self.philosophical_context,
            "framework_definition": self.framework_definition,
            "usage_count": self.usage_count,
            "first_used": self.first_used.isoformat() if self.first_used else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.extra_metadata or {}
        }

        if include_embedding and self.representative_embedding is not None:
            result["representative_embedding"] = self.representative_embedding

        return result


# ============================================================================
# UPDATE USER MODEL (add new relationships)
# ============================================================================

# Note: This assumes the User model exists from the original db_models.py
# We need to add these relationships to the existing User class

"""
Add to User class in db_models.py:

collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
chunks = relationship("Chunk", back_populates="user", cascade="all, delete-orphan")
media = relationship("Media", back_populates="user", cascade="all, delete-orphan")
belief_frameworks = relationship("BeliefFramework", back_populates="user", cascade="all, delete-orphan")
"""
