"""Database models for SQLAlchemy."""

from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class TransformationStatusEnum(str, enum.Enum):
    """Transformation status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CHECKPOINTED = "checkpointed"


class Transformation(Base):
    """Transformation job record."""
    
    __tablename__ = "transformations"
    
    id = Column(String, primary_key=True)
    status = Column(Enum(TransformationStatusEnum), default=TransformationStatusEnum.PENDING)
    progress = Column(Float, default=0.0)
    
    # Content
    original_content = Column(Text, nullable=False)
    transformed_content = Column(Text, nullable=True)
    
    # Parameters
    persona = Column(String, nullable=False)
    namespace = Column(String, nullable=False)
    style = Column(String, nullable=False)
    depth = Column(Float, default=0.5)
    preserve_structure = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error = Column(Text, nullable=True)
    
    # Relationships
    checkpoints = relationship("Checkpoint", back_populates="transformation", cascade="all, delete-orphan")


class Checkpoint(Base):
    """Checkpoint for transformation state."""
    
    __tablename__ = "checkpoints"
    
    id = Column(String, primary_key=True)
    transformation_id = Column(String, ForeignKey("transformations.id"), nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transformation = relationship("Transformation", back_populates="checkpoints")


class Session(Base):
    """Agent session for memory persistence."""
    
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    transformation_id = Column(String, ForeignKey("transformations.id"), nullable=False)
    context = Column(Text, nullable=True)
    memory_files = Column(Text, nullable=True)  # JSON array of file paths
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
