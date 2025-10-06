"""
SQLAlchemy models for transformation pipeline.

This module defines the ORM models for batch transformation jobs,
chunk transformations, and transformation lineage tracking.

Supports:
- Batch transformation jobs with progress tracking
- Linking source chunks to transformed results
- Multi-generation transformation lineage
- Cross-session content evolution
- Graph-based provenance queries
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, ForeignKey,
    DateTime, Float, BigInteger, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import enum

# Import Base from db_models to ensure proper relationships
from models.db_models import Base, User
from models.chunk_models import Chunk


# ============================================================================
# ENUMS
# ============================================================================

class JobStatus(str, enum.Enum):
    """Transformation job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    """Types of transformation jobs."""
    PERSONA_TRANSFORM = "persona_transform"
    MADHYAMAKA_DETECT = "madhyamaka_detect"
    MADHYAMAKA_TRANSFORM = "madhyamaka_transform"
    PERSPECTIVES = "perspectives"
    CONTEMPLATION = "contemplation"
    CUSTOM = "custom"


# ============================================================================
# TRANSFORMATION JOB MODEL
# ============================================================================

class TransformationJob(Base):
    """
    Batch transformation job for processing multiple chunks.

    Tracks progress, configuration, and status of long-running
    transformation operations.
    """

    __tablename__ = "transformation_jobs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)

    # Identity
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    job_type = Column(String(50), nullable=False)

    # Status and progress
    status = Column(String(50), default="pending", nullable=False)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    current_item_id = Column(UUID(as_uuid=True), nullable=True)  # Current chunk being processed

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)

    # Configuration
    configuration = Column(JSONB, default={}, nullable=False)
    # Example configuration:
    # {
    #   "persona": "scientist",
    #   "namespace": "academic",
    #   "style": "formal",
    #   "depth": 0.7,
    #   "preserve_structure": true,
    #   "source_chunk_ids": ["uuid1", "uuid2", ...],
    #   "source_message_ids": ["uuid3", "uuid4", ...],
    #   "source_collection_id": "uuid5"
    # }

    # Execution metadata
    tokens_used = Column(BigInteger, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    processing_time_ms = Column(BigInteger, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Priority (for queue ordering)
    priority = Column(Integer, default=0)  # Higher = more important

    # Flexible metadata
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')

    # Relationships
    user = relationship("User", backref="transformation_jobs")
    session = relationship("Session", backref="transformation_jobs")
    chunk_transformations = relationship(
        "ChunkTransformation",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    def to_dict(self, include_config: bool = True, include_transformations: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "session_id": str(self.session_id) if self.session_id else None,
            "name": self.name,
            "description": self.description,
            "job_type": self.job_type.value,
            "status": self.status.value,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "progress_percentage": self.progress_percentage,
            "current_item_id": str(self.current_item_id) if self.current_item_id else None,
            "error_message": self.error_message,
            "error_count": self.error_count,
            "tokens_used": self.tokens_used,
            "estimated_cost_usd": self.estimated_cost_usd,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "priority": self.priority,
            "metadata": self.extra_metadata or {}
        }

        if include_config:
            result["configuration"] = self.configuration or {}

        if include_transformations:
            result["transformations"] = [t.to_dict() for t in self.chunk_transformations]

        return result


# ============================================================================
# CHUNK TRANSFORMATION MODEL
# ============================================================================

class ChunkTransformation(Base):
    """
    Links source chunks to their transformed results.

    Tracks individual transformation operations within a job,
    preserving parameters and creating relationships for graph queries.
    """

    __tablename__ = "chunk_transformations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job reference
    job_id = Column(UUID(as_uuid=True), ForeignKey("transformation_jobs.id", ondelete="CASCADE"), nullable=False)

    # Source and result
    source_chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)
    result_chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)

    # Link to old transformation system (for continuity)
    transformation_id = Column(UUID(as_uuid=True), ForeignKey("transformations.id", ondelete="SET NULL"), nullable=True)

    # Transformation type and parameters
    transformation_type = Column(String(100), nullable=False)
    # Examples: "persona_transform", "madhyamaka_detect", "perspectives"

    parameters = Column(JSONB, default={}, nullable=False)
    # Example parameters:
    # {
    #   "persona": "scientist",
    #   "namespace": "academic",
    #   "style": "formal",
    #   "depth": 0.7,
    #   "preserve_structure": true
    # }

    # Status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Execution metadata
    tokens_used = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Sequence in job
    sequence_number = Column(Integer, nullable=True)

    # Flexible metadata
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')

    # Relationships
    job = relationship("TransformationJob", back_populates="chunk_transformations")
    source_chunk = relationship("Chunk", foreign_keys=[source_chunk_id], backref="source_transformations")
    result_chunk = relationship("Chunk", foreign_keys=[result_chunk_id], backref="result_transformations")
    transformation = relationship("Transformation", backref="chunk_transformations")

    def to_dict(self, include_chunks: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "job_id": str(self.job_id),
            "source_chunk_id": str(self.source_chunk_id),
            "result_chunk_id": str(self.result_chunk_id) if self.result_chunk_id else None,
            "transformation_id": str(self.transformation_id) if self.transformation_id else None,
            "transformation_type": self.transformation_type,
            "parameters": self.parameters or {},
            "status": self.status,
            "error_message": self.error_message,
            "tokens_used": self.tokens_used,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "sequence_number": self.sequence_number,
            "metadata": self.extra_metadata or {}
        }

        if include_chunks:
            if self.source_chunk:
                result["source_chunk"] = self.source_chunk.to_dict()
            if self.result_chunk:
                result["result_chunk"] = self.result_chunk.to_dict()

        return result


# ============================================================================
# TRANSFORMATION LINEAGE MODEL
# ============================================================================

class TransformationLineage(Base):
    """
    Tracks multi-generation transformation lineage for graph visualization.

    Maps transformation chains from original content through multiple
    transformations, across sessions, with full provenance tracking.
    """

    __tablename__ = "transformation_lineage"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Root content
    root_chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)

    # Current chunk in lineage
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)

    # Generation tracking
    generation = Column(Integer, default=0, nullable=False)
    # 0 = original content
    # 1 = first transformation
    # 2 = transformation of transformation
    # etc.

    # Transformation path
    transformation_path = Column(ARRAY(Text), default=[], nullable=False)
    # Example: ["persona→scientist", "madhyamaka→detect", "perspectives→poet"]

    # Parent in lineage (immediate predecessor)
    parent_lineage_id = Column(UUID(as_uuid=True), ForeignKey("transformation_lineage.id", ondelete="SET NULL"), nullable=True)

    # Session tracking
    session_ids = Column(ARRAY(UUID(as_uuid=True)), default=[], nullable=False)
    # Tracks all sessions that contributed to this lineage branch

    # Job tracking
    job_ids = Column(ARRAY(UUID(as_uuid=True)), default=[], nullable=False)
    # All transformation jobs in this lineage

    # Graph metadata
    depth = Column(Integer, default=0)  # Distance from root
    branch_id = Column(UUID(as_uuid=True), nullable=True)  # Identifies parallel branches

    # Statistics
    total_transformations = Column(Integer, default=0)
    total_tokens_used = Column(BigInteger, default=0)

    # Flexible metadata
    extra_metadata = Column(JSONB, default={}, nullable=False, name='metadata')
    # Can store:
    # - transformation_types: ["persona", "madhyamaka", "perspectives"]
    # - personas_used: ["scientist", "poet", "skeptic"]
    # - frameworks: [{"persona": "X", "namespace": "Y", "style": "Z"}]

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    root_chunk = relationship("Chunk", foreign_keys=[root_chunk_id], backref="lineage_as_root")
    chunk = relationship("Chunk", foreign_keys=[chunk_id], backref="lineage")
    parent = relationship("TransformationLineage", remote_side=[id], backref="children")

    def to_dict(self, include_chunks: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "root_chunk_id": str(self.root_chunk_id),
            "chunk_id": str(self.chunk_id),
            "generation": self.generation,
            "transformation_path": self.transformation_path or [],
            "parent_lineage_id": str(self.parent_lineage_id) if self.parent_lineage_id else None,
            "session_ids": [str(sid) for sid in self.session_ids] if self.session_ids else [],
            "job_ids": [str(jid) for jid in self.job_ids] if self.job_ids else [],
            "depth": self.depth,
            "branch_id": str(self.branch_id) if self.branch_id else None,
            "total_transformations": self.total_transformations,
            "total_tokens_used": self.total_tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.extra_metadata or {}
        }

        if include_chunks:
            if self.root_chunk:
                result["root_chunk"] = self.root_chunk.to_dict()
            if self.chunk:
                result["chunk"] = self.chunk.to_dict()

        return result
