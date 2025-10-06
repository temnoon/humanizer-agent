"""
SQLAlchemy models for book builder system.

Enables users to organize transformed content into structured books/papers.
Inspired by Joplin's notebook structure but focused on academic/technical writing.
"""

from sqlalchemy import (
    Column, String, Integer, Text, ForeignKey, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from models.db_models import Base, User
from models.chunk_models import Chunk
from models.pipeline_models import TransformationJob


# ============================================================================
# BOOK MODEL
# ============================================================================

class Book(Base):
    """
    Top-level container for papers, books, articles, reports.

    Similar to Joplin's Notebook but focused on long-form writing with
    export to LaTeX/PDF for academic and technical publishing.
    """

    __tablename__ = "books"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Identity
    title = Column(String(500), nullable=False)
    subtitle = Column(Text, nullable=True)
    book_type = Column(String(50), nullable=False, default='paper')
    # Types: 'paper', 'book', 'article', 'report', 'thesis', 'documentation'

    # Configuration (TOML-assisted UI → JSONB storage)
    configuration = Column(JSONB, default={}, nullable=False)
    # Example configuration:
    # {
    #   "document": {"type": "academic_paper", "template": "ieee"},
    #   "latex": {"documentclass": "article", "packages": ["amsmath"]},
    #   "pdf": {"paper_size": "letter", "margin": "1in"},
    #   "export": {"include_lineage": true, "include_metadata": false}
    # }

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Flexible metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    custom_metadata = Column(JSONB, default={}, nullable=False)

    # Relationships
    user = relationship("User", backref="books")
    sections = relationship(
        "BookSection",
        back_populates="book",
        cascade="all, delete-orphan",
        order_by="BookSection.sequence_number"
    )

    def to_dict(self, include_sections: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "subtitle": self.subtitle,
            "book_type": self.book_type,
            "configuration": self.configuration or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "custom_metadata": self.custom_metadata or {}
        }

        if include_sections:
            result["sections"] = [s.to_dict() for s in self.sections]

        return result


# ============================================================================
# BOOK SECTION MODEL
# ============================================================================

class BookSection(Base):
    """
    Hierarchical sections within a book (chapters, sections, subsections).

    Similar to Joplin's note structure but organized for structured documents.
    Supports nesting for complex hierarchies (Part I → Chapter 1 → Section 1.1).
    """

    __tablename__ = "book_sections"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Book reference
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)

    # Hierarchical structure
    parent_section_id = Column(UUID(as_uuid=True), ForeignKey("book_sections.id", ondelete="CASCADE"), nullable=True)

    # Identity
    title = Column(String(500), nullable=False)
    section_type = Column(String(50), nullable=True)
    # Types: 'part', 'chapter', 'section', 'subsection', 'appendix'

    sequence_number = Column(Integer, nullable=False)
    # Ordering within parent (or book if top-level)

    # Content (markdown)
    content = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Flexible metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    custom_metadata = Column(JSONB, default={}, nullable=False)

    # Relationships
    book = relationship("Book", back_populates="sections")
    parent = relationship("BookSection", remote_side=[id], backref="children")
    content_links = relationship(
        "BookContentLink",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="BookContentLink.sequence_number"
    )

    def to_dict(self, include_children: bool = False, include_content: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "book_id": str(self.book_id),
            "parent_section_id": str(self.parent_section_id) if self.parent_section_id else None,
            "title": self.title,
            "section_type": self.section_type,
            "sequence_number": self.sequence_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "custom_metadata": self.custom_metadata or {}
        }

        if include_content:
            result["content"] = self.content

        if include_children:
            result["children"] = [c.to_dict(include_children=True) for c in self.children]

        return result


# ============================================================================
# BOOK CONTENT LINK MODEL
# ============================================================================

class BookContentLink(Base):
    """
    Links chunks or transformation results to book sections.

    Allows users to:
    - Add original chunks to sections
    - Add transformation results to sections
    - Maintain provenance of content sources
    - Reorder content within sections
    """

    __tablename__ = "book_content_links"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Section reference
    section_id = Column(UUID(as_uuid=True), ForeignKey("book_sections.id", ondelete="CASCADE"), nullable=False)

    # Content sources (one of these should be set)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    transformation_job_id = Column(UUID(as_uuid=True), ForeignKey("transformation_jobs.id", ondelete="SET NULL"), nullable=True)

    # Ordering and notes
    sequence_number = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    section = relationship("BookSection", back_populates="content_links")
    chunk = relationship("Chunk", backref="book_links")
    transformation_job = relationship("TransformationJob", backref="book_links")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "section_id": str(self.section_id),
            "chunk_id": str(self.chunk_id) if self.chunk_id else None,
            "transformation_job_id": str(self.transformation_job_id) if self.transformation_job_id else None,
            "sequence_number": self.sequence_number,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
