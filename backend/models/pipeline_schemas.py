"""
Pydantic schemas for transformation pipeline API.

Provides type-safe request/response models for:
- Job creation and management
- Batch transformations
- Lineage and provenance queries
- Graph data structures
"""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from uuid import UUID


# ============================================================================
# ENUMS
# ============================================================================

class JobStatusEnum(str, Enum):
    """Transformation job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class JobTypeEnum(str, Enum):
    """Types of transformation jobs."""
    PERSONA_TRANSFORM = "persona_transform"
    MADHYAMAKA_DETECT = "madhyamaka_detect"
    MADHYAMAKA_TRANSFORM = "madhyamaka_transform"
    PERSPECTIVES = "perspectives"
    CONTEMPLATION = "contemplation"
    CUSTOM = "custom"


class RelationshipTypeEnum(str, Enum):
    """Types of chunk relationships."""
    TRANSFORMS_INTO = "transforms_into"
    DERIVES_FROM = "derives_from"
    CITES = "cites"
    RESPONDS_TO = "responds_to"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    CONTRASTS_WITH = "contrasts_with"


# ============================================================================
# JOB CREATION AND CONFIGURATION
# ============================================================================

class TransformationConfig(BaseModel):
    """Configuration for a transformation."""
    persona: Optional[str] = Field(None, description="Target persona/voice")
    namespace: Optional[str] = Field(None, description="Conceptual framework/domain")
    style: Optional[str] = Field(None, description="Writing style")
    depth: float = Field(default=0.5, ge=0.0, le=1.0, description="Transformation depth")
    preserve_structure: bool = Field(default=True, description="Maintain original structure")

    # Madhyamaka-specific
    num_alternatives: Optional[int] = Field(None, ge=1, le=10, description="Number of alternatives")
    user_stage: Optional[int] = Field(None, ge=1, le=5, description="User journey stage")

    # Perspectives-specific
    num_perspectives: Optional[int] = Field(None, ge=2, le=5, description="Number of perspectives")

    # Custom parameters
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="Custom transformation parameters")


class JobCreateRequest(BaseModel):
    """Request to create a transformation job."""
    name: str = Field(..., min_length=1, max_length=500, description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    job_type: JobTypeEnum = Field(..., description="Type of transformation")

    # Source selection
    source_chunk_ids: Optional[List[UUID]] = Field(None, description="Specific chunks to transform")
    source_message_ids: Optional[List[UUID]] = Field(None, description="Messages to transform (all chunks)")
    source_collection_id: Optional[UUID] = Field(None, description="Collection to transform (all chunks)")

    # Configuration
    configuration: TransformationConfig = Field(..., description="Transformation parameters")

    # Session (optional)
    session_id: Optional[UUID] = Field(None, description="Session to associate with")

    # Priority
    priority: int = Field(default=0, description="Job priority (higher = more important)")

    @model_validator(mode='after')
    def validate_source(self):
        """Ensure at least one source is specified."""
        if not any([self.source_chunk_ids, self.source_message_ids, self.source_collection_id]):
            raise ValueError("Must specify at least one source: chunk_ids, message_ids, or collection_id")

        return self


class JobCreateResponse(BaseModel):
    """Response after creating a job."""
    id: UUID = Field(..., description="Job ID")
    name: str
    job_type: str
    status: str
    total_items: int
    created_at: datetime
    message: str = Field(default="Job created successfully")


# ============================================================================
# JOB STATUS AND PROGRESS
# ============================================================================

class JobProgress(BaseModel):
    """Job progress information."""
    total_items: int
    processed_items: int
    failed_items: int
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    current_item_id: Optional[UUID] = None


class JobStatusResponse(BaseModel):
    """Detailed job status."""
    id: UUID
    name: str
    description: Optional[str]
    job_type: str
    status: str

    # Progress
    progress: JobProgress

    # Configuration
    configuration: Dict[str, Any]

    # Execution metadata
    tokens_used: int
    estimated_cost_usd: float
    processing_time_ms: int

    # Error tracking
    error_message: Optional[str]
    error_count: int

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    # Priority
    priority: int

    # Metadata
    metadata: Dict[str, Any]


class JobListResponse(BaseModel):
    """List of jobs."""
    jobs: List[JobStatusResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# BATCH TRANSFORMATION
# ============================================================================

class BatchTransformRequest(BaseModel):
    """Request to transform multiple chunks."""
    chunk_ids: List[UUID] = Field(..., min_items=1, description="Chunks to transform")
    transformation_type: str = Field(..., description="Type of transformation")
    parameters: TransformationConfig = Field(..., description="Transformation parameters")

    # Job options
    job_name: Optional[str] = Field(None, description="Optional job name")
    session_id: Optional[UUID] = Field(None, description="Session to associate with")
    priority: int = Field(default=0, description="Job priority")


class BatchTransformResponse(BaseModel):
    """Response after starting batch transformation."""
    job_id: UUID
    total_chunks: int
    message: str


# ============================================================================
# LINEAGE AND PROVENANCE
# ============================================================================

class LineageNode(BaseModel):
    """Node in transformation lineage tree."""
    id: UUID
    chunk_id: UUID
    root_chunk_id: UUID
    generation: int
    transformation_path: List[str]
    depth: int
    content_preview: Optional[str] = Field(None, description="First 200 chars of content")
    metadata: Dict[str, Any]


class LineageResponse(BaseModel):
    """Transformation lineage for a chunk."""
    chunk_id: UUID
    ancestors: List[LineageNode]
    descendants: List[LineageNode]
    root_chunk_id: UUID
    total_generations: int


class ProvenanceChain(BaseModel):
    """Full provenance chain for a chunk."""
    chunk_id: UUID
    chain: List[LineageNode]
    total_transformations: int
    total_tokens_used: int
    sessions: List[UUID]
    jobs: List[UUID]


# ============================================================================
# GRAPH VISUALIZATION
# ============================================================================

class GraphNode(BaseModel):
    """Node in transformation graph."""
    id: UUID
    chunk_id: UUID
    content: str
    content_preview: str = Field(..., description="First 200 chars")
    generation: int
    transformation_type: Optional[str]
    metadata: Dict[str, Any]

    # Visual properties
    node_type: str = Field(default="chunk", description="Node type for visualization")
    color: Optional[str] = Field(None, description="Node color")
    size: Optional[int] = Field(None, description="Node size")


class GraphEdge(BaseModel):
    """Edge in transformation graph."""
    id: Optional[UUID] = None
    source: UUID = Field(..., description="Source node ID")
    target: UUID = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Type of relationship")
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Visual properties
    label: Optional[str] = Field(None, description="Edge label")
    color: Optional[str] = Field(None, description="Edge color")
    thickness: Optional[int] = Field(None, description="Edge thickness")


class TransformationGraph(BaseModel):
    """Complete transformation graph."""
    root_chunk_id: UUID
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Statistics
    total_nodes: int
    total_edges: int
    max_generation: int
    total_transformations: int


class SessionGraphRequest(BaseModel):
    """Request for session transformation graph."""
    session_id: UUID
    include_content: bool = Field(default=False, description="Include full chunk content")
    max_generation: Optional[int] = Field(None, description="Limit to N generations")


class CollectionGraphRequest(BaseModel):
    """Request for collection transformation graph."""
    collection_id: UUID
    include_content: bool = Field(default=False, description="Include full chunk content")
    max_generation: Optional[int] = Field(None, description="Limit to N generations")
    filter_by_job_type: Optional[JobTypeEnum] = Field(None, description="Filter by job type")


# ============================================================================
# RELATIONSHIPS
# ============================================================================

class ChunkRelationshipCreate(BaseModel):
    """Request to create a chunk relationship."""
    source_chunk_id: UUID
    target_chunk_id: UUID
    relationship_type: RelationshipTypeEnum
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkRelationshipResponse(BaseModel):
    """Chunk relationship response."""
    id: UUID
    source_chunk_id: UUID
    target_chunk_id: UUID
    relationship_type: str
    strength: float
    metadata: Dict[str, Any]
    created_at: datetime


class RelationshipMapRequest(BaseModel):
    """Request for relationship map."""
    chunk_id: UUID
    relationship_types: Optional[List[RelationshipTypeEnum]] = Field(None, description="Filter by types")
    max_depth: int = Field(default=2, ge=1, le=5, description="Maximum traversal depth")


class RelationshipMapResponse(BaseModel):
    """Relationship map for a chunk."""
    center_chunk_id: UUID
    relationships: List[ChunkRelationshipResponse]
    related_chunks: List[UUID]
    graph: TransformationGraph


# ============================================================================
# JOB CONTROL
# ============================================================================

class JobControlRequest(BaseModel):
    """Request to control a job (pause/resume/cancel)."""
    action: str = Field(..., description="Action: start, pause, resume, cancel")

    @validator('action')
    def validate_action(cls, v):
        """Validate action value."""
        allowed = ['start', 'pause', 'resume', 'cancel']
        if v not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v


class JobControlResponse(BaseModel):
    """Response after job control action."""
    job_id: UUID
    status: str
    message: str


# ============================================================================
# TIMELINE VIEW
# ============================================================================

class TimelineEvent(BaseModel):
    """Event in transformation timeline."""
    timestamp: datetime
    event_type: str = Field(..., description="Type: job_created, transformation_completed, etc.")
    job_id: Optional[UUID]
    chunk_id: Optional[UUID]
    transformation_type: Optional[str]
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineRequest(BaseModel):
    """Request for transformation timeline."""
    session_id: Optional[UUID] = Field(None, description="Filter by session")
    collection_id: Optional[UUID] = Field(None, description="Filter by collection")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    limit: int = Field(default=100, ge=1, le=1000)


class TimelineResponse(BaseModel):
    """Transformation timeline response."""
    events: List[TimelineEvent]
    total_events: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]


# ============================================================================
# ERROR RESPONSE
# ============================================================================

class PipelineErrorResponse(BaseModel):
    """Error response for pipeline API."""
    error: str
    detail: Optional[str] = None
    job_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_code: Optional[str] = None
