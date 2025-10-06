"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TransformationStyle(str, Enum):
    """Available transformation styles."""
    FORMAL = "formal"
    CASUAL = "casual"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    JOURNALISTIC = "journalistic"


class TransformationStatusEnum(str, Enum):
    """Transformation processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CHECKPOINTED = "checkpointed"


class TransformationRequest(BaseModel):
    """Request to transform a narrative."""

    content: str = Field(..., description="Text content to transform")
    persona: str = Field(..., description="Target persona/voice")
    namespace: str = Field(..., description="Conceptual framework/domain")
    style: TransformationStyle = Field(..., description="Writing style")
    preserve_structure: bool = Field(
        default=True,
        description="Maintain original structure"
    )
    depth: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Transformation depth (0=minimal, 1=deep)"
    )
    user_tier: str = Field(
        default="free",
        description="User subscription tier (free or premium)"
    )
    # Session integration
    session_id: Optional[str] = Field(None, description="Session ID to associate transformation with")
    user_id: Optional[str] = Field(None, description="User ID for the transformation")


class TransformationResponse(BaseModel):
    """Response from transformation request."""
    
    id: str = Field(..., description="Transformation job ID")
    status: TransformationStatusEnum
    created_at: datetime
    message: str = Field(default="Transformation started")


class TransformationStatus(BaseModel):
    """Status of a transformation job."""
    
    id: str
    status: TransformationStatusEnum
    progress: float = Field(ge=0.0, le=1.0, description="Completion percentage")
    original_content: str
    transformed_content: Optional[str] = None
    persona: str
    namespace: str
    style: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    checkpoints: List[str] = Field(default_factory=list)


class TransformationResult(BaseModel):
    """Final transformation result."""
    
    id: str
    original_content: str
    transformed_content: str
    persona: str
    namespace: str
    style: str
    metadata: dict = Field(default_factory=dict)
    completed_at: datetime


class CheckpointCreate(BaseModel):
    """Request to create a checkpoint."""
    
    name: Optional[str] = Field(None, description="Checkpoint name")


class CheckpointResponse(BaseModel):
    """Checkpoint creation response."""
    
    checkpoint_id: str
    name: str
    created_at: datetime
    message: str


class RollbackRequest(BaseModel):
    """Request to rollback to a checkpoint."""
    
    checkpoint_id: str


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
