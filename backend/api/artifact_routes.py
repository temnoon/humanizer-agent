"""
Artifact API Routes

Endpoints for creating, retrieving, searching, and managing artifacts.

Artifacts are persistent semantic outputs from operations:
- Extractions, reports, summaries
- Transformations, comparisons
- Cluster analyses, trajectories
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from services.artifact_service import ArtifactService
from models.artifact_models import Artifact

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])

# Default user ID (from CLAUDE.md)
DEFAULT_USER_ID = "c7a31f8e-91e3-47e6-bea5-e33d0f35072d"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateArtifactRequest(BaseModel):
    """Request to create a new artifact."""

    artifact_type: str = Field(..., description="Type: report, extraction, cluster_summary, etc.")
    operation: str = Field(..., description="Operation that created this: semantic_search, etc.")
    content: str = Field(..., description="The actual content")
    content_format: str = Field("markdown", description="Format: markdown, json, html, plaintext")

    # Provenance
    source_chunk_ids: Optional[List[str]] = Field(None, description="Source chunk UUIDs")
    source_artifact_ids: Optional[List[str]] = Field(None, description="Source artifact UUIDs")
    source_operation_params: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")

    # Lineage
    parent_artifact_id: Optional[str] = Field(None, description="Parent artifact if refinement")

    # Metadata
    generation_model: Optional[str] = Field(None, description="Model used: claude-sonnet-4.5, etc.")
    generation_prompt: Optional[str] = Field(None, description="Prompt used for generation")
    topics: Optional[List[str]] = Field(None, description="Topics/tags")
    frameworks: Optional[List[str]] = Field(None, description="Frameworks applied")
    custom_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    # Options
    auto_embed: bool = Field(True, description="Auto-generate embedding")
    user_id: Optional[str] = Field(None, description="User ID (defaults to system user)")

    class Config:
        json_schema_extra = {
            "example": {
                "artifact_type": "extraction",
                "operation": "paragraph_extract",
                "content": "The three most relevant paragraphs about Madhyamaka...",
                "source_chunk_ids": ["uuid1", "uuid2"],
                "source_operation_params": {
                    "anchor_query": "madhyamaka emptiness",
                    "min_length": 100
                },
                "topics": ["madhyamaka", "buddhism"],
                "auto_embed": True
            }
        }


class UpdateArtifactRequest(BaseModel):
    """Request to update artifact fields."""

    is_approved: Optional[bool] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_notes: Optional[str] = None
    topics: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class ArtifactResponse(BaseModel):
    """Response containing artifact data."""

    id: str
    user_id: str
    artifact_type: str
    operation: str
    content: str
    content_format: str
    token_count: Optional[int]
    generation_model: Optional[str]
    topics: List[str]
    frameworks: List[str]
    sentiment: Optional[float]
    complexity_score: Optional[float]
    is_approved: bool
    user_rating: Optional[int]
    parent_artifact_id: Optional[str]
    lineage_depth: int
    source_chunk_ids: List[str]
    source_artifact_ids: List[str]
    source_operation_params: Dict[str, Any]
    created_at: str
    updated_at: str
    custom_metadata: Dict[str, Any]


class ArtifactListResponse(BaseModel):
    """Response for artifact listing."""

    artifacts: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class ArtifactSearchResponse(BaseModel):
    """Response for semantic search."""

    artifacts: List[Dict[str, Any]]
    query: str
    total: int


class LineageResponse(BaseModel):
    """Response for lineage tree."""

    artifact: Dict[str, Any]
    ancestors: List[Dict[str, Any]]
    descendants: Dict[str, Any]
    lineage_depth: int
    total_ancestors: int
    total_descendants: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/save", response_model=ArtifactResponse)
async def create_artifact(
    request: CreateArtifactRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new artifact.

    This endpoint saves any semantic output as a persistent, addressable artifact
    that can be:
    - Searched semantically
    - Referenced in future operations
    - Iterated on through transformations
    - Traced through lineage

    **Philosophy**: Makes the construction of meaning explicit and traceable.
    """
    try:
        service = ArtifactService()

        user_id = request.user_id or DEFAULT_USER_ID

        artifact = await service.create_artifact(
            session=db,
            user_id=user_id,
            artifact_type=request.artifact_type,
            operation=request.operation,
            content=request.content,
            content_format=request.content_format,
            source_chunk_ids=request.source_chunk_ids,
            source_artifact_ids=request.source_artifact_ids,
            source_operation_params=request.source_operation_params,
            parent_artifact_id=request.parent_artifact_id,
            generation_model=request.generation_model,
            generation_prompt=request.generation_prompt,
            topics=request.topics,
            frameworks=request.frameworks,
            custom_metadata=request.custom_metadata,
            auto_embed=request.auto_embed
        )

        logger.info(f"Created artifact: {artifact.id} (type={request.artifact_type})")

        return artifact.to_dict()

    except Exception as e:
        logger.error(f"Failed to create artifact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create artifact: {str(e)}")


@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "artifacts"}


@router.get("/search", response_model=ArtifactSearchResponse)
async def search_artifacts(
    query: str = Query(..., description="Search query"),
    user_id: Optional[str] = Query(None, description="User ID"),
    artifact_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Semantic search over artifacts.

    Uses pgvector cosine similarity to find artifacts semantically similar
    to the query text.

    **Use case**: Find all reports about "madhyamaka" or all transformations
    related to "consciousness work".
    """
    try:
        service = ArtifactService()

        results = await service.search_artifacts(
            session=db,
            user_id=user_id or DEFAULT_USER_ID,
            query_text=query,
            artifact_type=artifact_type,
            limit=limit
        )

        return {
            "artifacts": results,
            "query": query,
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"Failed to search artifacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search artifacts: {str(e)}")


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get artifact by ID.

    Returns full artifact with content, metadata, and provenance.
    """
    try:
        service = ArtifactService()

        artifact = await service.get_artifact(
            session=db,
            artifact_id=artifact_id,
            user_id=user_id or DEFAULT_USER_ID
        )

        if not artifact:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

        return artifact.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get artifact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get artifact: {str(e)}")


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    user_id: Optional[str] = Query(None, description="User ID"),
    artifact_type: Optional[str] = Query(None, description="Filter by type"),
    operation: Optional[str] = Query(None, description="Filter by operation"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    order_by: str = Query("created_at", description="Sort field"),
    order_dir: str = Query("desc", description="Sort direction (asc/desc)"),
    db: AsyncSession = Depends(get_db)
):
    """
    List artifacts with filters and pagination.

    Supports:
    - Filtering by type, operation
    - Sorting by any field
    - Pagination

    **Use case**: Browse all reports, extractions, or transformations.
    """
    try:
        service = ArtifactService()

        artifacts, total = await service.list_artifacts(
            session=db,
            user_id=user_id or DEFAULT_USER_ID,
            artifact_type=artifact_type,
            operation=operation,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir
        )

        return {
            "artifacts": [a.to_dict(include_content=False) for a in artifacts],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Failed to list artifacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list artifacts: {str(e)}")


@router.get("/{artifact_id}/lineage", response_model=LineageResponse)
async def get_artifact_lineage(
    artifact_id: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full lineage tree for an artifact.

    Returns:
    - Ancestors: All parent artifacts up to root
    - Descendants: All child artifacts (nested tree)
    - Lineage metadata

    **Use case**: Trace how an insight developed through iterations,
    or see all refinements of a base artifact.
    """
    try:
        service = ArtifactService()

        lineage = await service.get_lineage(
            session=db,
            artifact_id=artifact_id,
            user_id=user_id or DEFAULT_USER_ID
        )

        if not lineage:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

        return lineage

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lineage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get lineage: {str(e)}")


@router.patch("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: str,
    request: UpdateArtifactRequest,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update artifact fields.

    Allows updating:
    - is_approved, user_rating, user_notes
    - topics, frameworks
    - custom_metadata

    Content and provenance fields are immutable.
    """
    try:
        service = ArtifactService()

        # Filter out None values
        updates = {k: v for k, v in request.dict().items() if v is not None}

        artifact = await service.update_artifact(
            session=db,
            artifact_id=artifact_id,
            user_id=user_id or DEFAULT_USER_ID,
            updates=updates
        )

        if not artifact:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

        return artifact.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update artifact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update artifact: {str(e)}")


@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an artifact.

    Note: This will also set parent_artifact_id to NULL for any child artifacts
    (due to ON DELETE SET NULL constraint).
    """
    try:
        service = ArtifactService()

        deleted = await service.delete_artifact(
            session=db,
            artifact_id=artifact_id,
            user_id=user_id or DEFAULT_USER_ID
        )

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

        return {"status": "success", "message": f"Artifact {artifact_id} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete artifact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete artifact: {str(e)}")
