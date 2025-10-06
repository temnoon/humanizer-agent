"""SQLAlchemy models for PostgreSQL + pgvector."""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, ForeignKey,
    DateTime, JSON, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

Base = declarative_base()


class User(Base):
    """User model - supports both authenticated and anonymous users."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True)
    username = Column(String(100), nullable=True)
    is_anonymous = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    preferences = Column(JSONB, default={}, name='preferences')

    # Relationships (legacy schema)
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    transformations = relationship("Transformation", back_populates="user", cascade="all, delete-orphan")
    belief_patterns = relationship("BeliefPattern", back_populates="user", cascade="all, delete-orphan")

    # Relationships (new chunk-based schema)
    # Note: Import chunk_models to use these relationships
    # collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    # messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    # chunks = relationship("Chunk", back_populates="user", cascade="all, delete-orphan")
    # media = relationship("Media", back_populates="user", cascade="all, delete-orphan")
    # belief_frameworks = relationship("BeliefFramework", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "is_anonymous": self.is_anonymous,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "preferences": self.preferences or {}
        }


class Session(Base):
    """Session model - groups related transformations."""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    extra_metadata = Column(JSONB, default={}, name='metadata')
    transformation_count = Column(Integer, default=0)
    is_archived = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
    transformations = relationship("Transformation", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self, include_transformations: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "transformation_count": self.transformation_count,
            "is_archived": self.is_archived,
            "metadata": self.extra_metadata or {}
        }

        if include_transformations:
            result["transformations"] = [t.to_dict() for t in self.transformations]

        return result


class Transformation(Base):
    """Transformation model with vector embeddings."""

    __tablename__ = "transformations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    # Source content
    source_text = Column(Text, nullable=False)
    source_embedding = Column(Vector(1536), nullable=True)

    # Transformation parameters (Symbolic Realm)
    persona = Column(String(100), nullable=False)
    namespace = Column(String(100), nullable=False)
    style = Column(String(100), nullable=False)

    # Transformed content
    transformed_content = Column(Text, nullable=True)
    transformed_embedding = Column(Vector(1536), nullable=True)

    # Philosophical metadata
    belief_framework = Column(JSONB, nullable=True)
    emotional_profile = Column(Text, nullable=True)
    philosophical_context = Column(Text, nullable=True)

    # Execution metadata
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relational tracking
    parent_transformation_id = Column(UUID(as_uuid=True), ForeignKey("transformations.id", ondelete="SET NULL"), nullable=True)
    is_checkpoint = Column(Boolean, default=False)

    # Full metadata capture
    extra_metadata = Column(JSONB, default={}, name='metadata')

    # Relationships
    session = relationship("Session", back_populates="transformations")
    user = relationship("User", back_populates="transformations")
    parent = relationship("Transformation", remote_side=[id], backref="children")

    def to_dict(self, include_embeddings: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "user_id": str(self.user_id),
            "source_text": self.source_text,
            "persona": self.persona,
            "namespace": self.namespace,
            "style": self.style,
            "transformed_content": self.transformed_content,
            "belief_framework": self.belief_framework,
            "emotional_profile": self.emotional_profile,
            "philosophical_context": self.philosophical_context,
            "status": self.status,
            "error_message": self.error_message,
            "tokens_used": self.tokens_used,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parent_transformation_id": str(self.parent_transformation_id) if self.parent_transformation_id else None,
            "is_checkpoint": self.is_checkpoint,
            "metadata": self.extra_metadata or {}
        }

        if include_embeddings:
            result["source_embedding"] = self.source_embedding
            result["transformed_embedding"] = self.transformed_embedding

        return result


class BeliefPattern(Base):
    """Belief pattern tracking - identifies recurring frameworks."""

    __tablename__ = "belief_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    # Pattern identification
    pattern_name = Column(String(200), nullable=False)
    persona = Column(String(100), nullable=True)
    namespace = Column(String(100), nullable=True)
    style = Column(String(100), nullable=True)

    # Pattern analysis
    frequency_count = Column(Integer, default=1)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())

    # Representative embedding (centroid of all instances)
    pattern_embedding = Column(Vector(1536), nullable=True)

    # Insights
    philosophical_insight = Column(Text, nullable=True)
    emotional_signature = Column(Text, nullable=True)

    extra_metadata = Column(JSONB, default={}, name='metadata')

    # Relationships
    user = relationship("User", back_populates="belief_patterns")

    def to_dict(self, include_embedding: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "pattern_name": self.pattern_name,
            "persona": self.persona,
            "namespace": self.namespace,
            "style": self.style,
            "frequency_count": self.frequency_count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "philosophical_insight": self.philosophical_insight,
            "emotional_signature": self.emotional_signature,
            "metadata": self.extra_metadata or {}
        }

        if include_embedding:
            result["pattern_embedding"] = self.pattern_embedding

        return result
