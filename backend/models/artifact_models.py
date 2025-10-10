"""
SQLAlchemy models for Artifacts system.

Artifacts are persistent semantic outputs from operations like:
- Extractions (paragraphs, sentences, concepts)
- Cluster summaries
- Reports and syntheses
- Transformations
- Comparisons

Philosophy: Every generated output becomes an addressable, composable artifact
that can be iterated on, combined, and traced through lineage.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, ForeignKey,
    DateTime, Float, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from models.db_models import Base


# ============================================================================
# ARTIFACT MODEL
# ============================================================================

class Artifact(Base):
    """
    Persistent semantic output from any humanizer operation.

    Core capabilities:
    - Provenance tracking (what chunks/artifacts were used)
    - Lineage tracking (iterative refinement chains)
    - Semantic search (via embeddings)
    - Quality tracking (ratings, approval)
    - Composability (artifacts can reference other artifacts)

    Philosophy: Makes the construction of meaning explicit and traceable,
    embodying computational Madhyamaka - revealing dependent origination.
    """

    __tablename__ = "artifacts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Classification
    artifact_type = Column(String(50), nullable=False)
    # Types: 'report', 'extraction', 'cluster_summary', 'transformation',
    #        'synthesis', 'comparison', 'trajectory', 'graph', 'narrative'

    operation = Column(String(100), nullable=False)
    # What created this: 'semantic_search', 'paragraph_extract',
    #                   'cluster_analysis', 'progressive_summary', etc.

    # Content
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default='markdown')
    # Formats: 'markdown', 'json', 'html', 'plaintext'

    content_embedding = Column(Vector(1024), nullable=True)
    # For semantic search over artifacts themselves

    # Provenance (what created this)
    source_chunk_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    # Original chunks used as input

    source_artifact_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    # Other artifacts used as input (for composition)

    source_operation_params = Column(JSONB, nullable=True)
    # Parameters of the operation that created this

    # Lineage (iterative refinement)
    parent_artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)
    # If this artifact was created by refining another artifact

    lineage_depth = Column(Integer, default=0)
    # How many generations deep:
    # 0 = from chunks, 1 = from 1 artifact, 2 = from artifact of artifact, etc.

    # Quality metadata
    token_count = Column(Integer, nullable=True)
    generation_model = Column(String(100), nullable=True)
    # e.g., 'claude-sonnet-4.5', 'gpt-4', 'ollama:llama2'

    generation_prompt = Column(Text, nullable=True)
    # Store the prompt used to generate this (for reproducibility)

    # Semantic metadata
    topics = Column(ARRAY(Text), nullable=True)
    # Auto-extracted or manually tagged topics

    frameworks = Column(ARRAY(Text), nullable=True)
    # PERSONA/NAMESPACE/STYLE or philosophical frameworks

    sentiment = Column(Float, nullable=True)
    # -1.0 to 1.0

    complexity_score = Column(Float, nullable=True)
    # 0.0 to 1.0

    # User interaction
    is_approved = Column(Boolean, default=False)
    user_rating = Column(Integer, nullable=True)
    # 1-5 stars

    user_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Flexible metadata (using custom_metadata to avoid SQLAlchemy reserved name)
    custom_metadata = Column(JSONB, default={}, nullable=False)

    # Relationships
    user = relationship("User", backref="artifacts")
    parent = relationship("Artifact", remote_side=[id], backref="children")

    def to_dict(
        self,
        include_embedding: bool = False,
        include_content: bool = True,
        include_children: bool = False
    ) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "artifact_type": self.artifact_type,
            "operation": self.operation,
            "content_format": self.content_format,
            "token_count": self.token_count,
            "generation_model": self.generation_model,
            "topics": self.topics or [],
            "frameworks": self.frameworks or [],
            "sentiment": self.sentiment,
            "complexity_score": self.complexity_score,
            "is_approved": self.is_approved,
            "user_rating": self.user_rating,
            "parent_artifact_id": str(self.parent_artifact_id) if self.parent_artifact_id else None,
            "lineage_depth": self.lineage_depth,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "custom_metadata": self.custom_metadata or {}
        }

        if include_content:
            result["content"] = self.content
            result["generation_prompt"] = self.generation_prompt
            result["user_notes"] = self.user_notes

        # Convert UUIDs to strings for JSON serialization
        if self.source_chunk_ids:
            result["source_chunk_ids"] = [str(cid) for cid in self.source_chunk_ids]
        else:
            result["source_chunk_ids"] = []

        if self.source_artifact_ids:
            result["source_artifact_ids"] = [str(aid) for aid in self.source_artifact_ids]
        else:
            result["source_artifact_ids"] = []

        if self.source_operation_params:
            result["source_operation_params"] = self.source_operation_params
        else:
            result["source_operation_params"] = {}

        if include_embedding and self.content_embedding is not None:
            result["content_embedding"] = self.content_embedding

        if include_children and self.children:
            result["children"] = [c.to_dict(include_content=False) for c in self.children]

        return result

    def get_lineage_chain(self) -> List['Artifact']:
        """
        Get the full lineage chain from root to this artifact.

        Returns:
            List of artifacts from root (oldest) to this artifact (newest)
        """
        chain = [self]
        current = self

        # Walk up the parent chain
        while current.parent_artifact_id is not None and current.parent:
            current = current.parent
            chain.insert(0, current)

        return chain

    def get_descendant_tree(self, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """
        Get the full descendant tree from this artifact.

        Args:
            max_depth: Maximum depth to traverse (None = unlimited)

        Returns:
            Nested dictionary representing the tree
        """
        node = {
            "artifact": self.to_dict(include_content=False),
            "children": []
        }

        if max_depth is None or max_depth > 0:
            next_depth = None if max_depth is None else max_depth - 1
            for child in self.children:
                node["children"].append(child.get_descendant_tree(max_depth=next_depth))

        return node

    def __repr__(self):
        return f"<Artifact(id={self.id}, type='{self.artifact_type}', operation='{self.operation}')>"
