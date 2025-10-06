"""
API routes for transformation pipeline.

Endpoints:
- Job management (create, list, get, control)
- Batch transformations
- Lineage and provenance queries
- Graph visualization
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from database import get_db
from services.pipeline_service import PipelineService
from services.job_processor import process_transformation_job
from models.pipeline_models import JobStatus, JobType
from models.pipeline_schemas import (
    JobCreateRequest, JobCreateResponse, JobStatusResponse, JobListResponse,
    BatchTransformRequest, BatchTransformResponse,
    LineageResponse, ProvenanceChain, LineageNode,
    TransformationGraph, SessionGraphRequest, CollectionGraphRequest,
    JobControlRequest, JobControlResponse,
    TimelineRequest, TimelineResponse, TimelineEvent,
    RelationshipMapRequest, RelationshipMapResponse,
    PipelineErrorResponse
)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
pipeline_service = PipelineService()


# ============================================================================
# JOB MANAGEMENT
# ============================================================================

@router.post("/jobs", response_model=JobCreateResponse)
async def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new transformation job.

    Accepts:
    - source_chunk_ids: Specific chunks to transform
    - source_message_ids: Messages to transform (all chunks)
    - source_collection_id: Collection to transform (all chunks)

    At least one source must be specified.
    """
    try:
        # For now, use a test user ID (in production, get from auth)
        from models.db_models import User
        from sqlalchemy import select

        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="No user found. Create a user first.")

        job = await pipeline_service.create_job(db, user.id, request)

        # Start background processing
        background_tasks.add_task(process_transformation_job, job.id)

        return JobCreateResponse(
            id=job.id,
            name=job.name,
            job_type=job.job_type,
            status=job.status,
            total_items=job.total_items,
            created_at=job.created_at,
            message=f"Job created with {job.total_items} items to process"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = None,
    job_type: Optional[JobType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List transformation jobs with filters and pagination."""
    try:
        # For now, use first user (in production, get from auth)
        from models.db_models import User
        from sqlalchemy import select

        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="No user found")

        offset = (page - 1) * page_size
        jobs, total = await pipeline_service.list_jobs(
            db, user.id, status=status, job_type=job_type,
            limit=page_size, offset=offset
        )

        return JobListResponse(
            jobs=[JobStatusResponse(
                id=job.id,
                name=job.name,
                description=job.description,
                job_type=job.job_type,
                status=job.status,
                progress={
                    "total_items": job.total_items,
                    "processed_items": job.processed_items,
                    "failed_items": job.failed_items,
                    "progress_percentage": job.progress_percentage,
                    "current_item_id": job.current_item_id
                },
                configuration=job.configuration,
                tokens_used=job.tokens_used,
                estimated_cost_usd=job.estimated_cost_usd,
                processing_time_ms=job.processing_time_ms,
                error_message=job.error_message,
                error_count=job.error_count,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                updated_at=job.updated_at,
                priority=job.priority,
                metadata=job.extra_metadata or {}
            ) for job in jobs],
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed job status."""
    try:
        job = await pipeline_service.get_job(db, job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return JobStatusResponse(
            id=job.id,
            name=job.name,
            description=job.description,
            job_type=job.job_type,
            status=job.status,
            progress={
                "total_items": job.total_items,
                "processed_items": job.processed_items,
                "failed_items": job.failed_items,
                "progress_percentage": job.progress_percentage,
                "current_item_id": job.current_item_id
            },
            configuration=job.configuration,
            tokens_used=job.tokens_used,
            estimated_cost_usd=job.estimated_cost_usd,
            processing_time_ms=job.processing_time_ms,
            error_message=job.error_message,
            error_count=job.error_count,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            updated_at=job.updated_at,
            priority=job.priority,
            metadata=job.extra_metadata or {}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.post("/jobs/{job_id}/control", response_model=JobControlResponse)
async def control_job(
    job_id: UUID,
    request: JobControlRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Control a job (start, pause, resume, cancel)."""
    try:
        job = await pipeline_service.get_job(db, job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        action = request.action

        if action == "start" or action == "resume":
            if job.status in ["completed", "cancelled"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot {action} a {job.status} job"
                )

            job = await pipeline_service.update_job_status(db, job_id, "processing")
            # Start background processing
            background_tasks.add_task(process_transformation_job, job_id)
            message = f"Job {action}ed successfully"

        elif action == "pause":
            if job.status != "processing":
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot pause a {job.status} job"
                )

            job = await pipeline_service.update_job_status(db, job_id, "paused")
            message = "Job paused successfully"

        elif action == "cancel":
            if job.status in ["completed", "cancelled"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel a {job.status} job"
                )

            job = await pipeline_service.update_job_status(db, job_id, "cancelled")
            message = "Job cancelled successfully"

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

        return JobControlResponse(
            job_id=job.id,
            status=job.status,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to control job: {str(e)}")


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a job (only if not processing)."""
    try:
        job = await pipeline_service.get_job(db, job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job.status == JobStatus.PROCESSING:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a processing job. Pause or cancel it first."
            )

        await db.delete(job)
        await db.commit()

        return {"message": f"Job {job_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


@router.get("/jobs/{job_id}/results")
async def get_job_results(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the results (transformed chunks) of a completed job.

    Returns:
    - For persona_transform: transformed text chunks
    - For madhyamaka_detect: detection analysis
    - For madhyamaka_transform: middle path alternatives
    - For perspectives: multiple perspectives
    """
    try:
        from sqlalchemy import select
        from models.pipeline_models import TransformationJob, ChunkTransformation
        from models.chunk_models import Chunk

        # Get job
        job = await pipeline_service.get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Get all transformed chunks for this job
        result = await db.execute(
            select(ChunkTransformation, Chunk)
            .join(Chunk, ChunkTransformation.result_chunk_id == Chunk.id)
            .where(ChunkTransformation.job_id == job_id)
            .order_by(ChunkTransformation.sequence_number)
        )

        transformations = []
        for ct, chunk in result:
            # Get metadata (it's stored as extra_metadata in the model)
            metadata_dict = chunk.extra_metadata if chunk.extra_metadata else {}

            transformations.append({
                "source_chunk_id": str(ct.source_chunk_id),
                "result_chunk_id": str(ct.result_chunk_id),
                "transformation_type": ct.transformation_type,
                "sequence": ct.sequence_number,
                "content": chunk.content,
                "metadata": metadata_dict,
                "tokens_used": ct.tokens_used,
                "processing_time_ms": ct.processing_time_ms
            })

        # Convert configuration safely
        config_dict = {}
        if job.configuration:
            if isinstance(job.configuration, dict):
                config_dict = job.configuration
            elif hasattr(job.configuration, '__dict__'):
                config_dict = {k: v for k, v in job.configuration.__dict__.items()
                              if not k.startswith('_')}

        return {
            "job_id": str(job_id),
            "job_type": job.job_type,
            "job_name": job.name,
            "status": job.status,
            "configuration": config_dict,
            "results": transformations
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job results: {str(e)}")


# ============================================================================
# BATCH TRANSFORMATION
# ============================================================================

@router.post("/transform-batch", response_model=BatchTransformResponse)
async def transform_batch(
    request: BatchTransformRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Transform multiple chunks in a batch.

    This is a convenience endpoint that creates a job and starts processing.
    """
    try:
        # For now, use first user
        from models.db_models import User
        from sqlalchemy import select

        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="No user found")

        # Create job request
        job_request = JobCreateRequest(
            name=request.job_name or f"Batch {request.transformation_type}",
            description=f"Batch transformation of {len(request.chunk_ids)} chunks",
            job_type=JobType(request.transformation_type.split('_')[0]),  # Extract type
            source_chunk_ids=request.chunk_ids,
            configuration=request.parameters,
            session_id=request.session_id,
            priority=request.priority
        )

        job = await pipeline_service.create_job(db, user.id, job_request)

        # Start processing immediately
        background_tasks.add_task(process_transformation_job, job.id)

        return BatchTransformResponse(
            job_id=job.id,
            total_chunks=len(request.chunk_ids),
            message=f"Batch transformation started for {len(request.chunk_ids)} chunks"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch transformation: {str(e)}")


# ============================================================================
# LINEAGE AND PROVENANCE
# ============================================================================

@router.get("/lineage/{chunk_id}", response_model=LineageResponse)
async def get_lineage(
    chunk_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get transformation lineage for a chunk (ancestors and descendants)."""
    try:
        lineage_data = await pipeline_service.get_lineage(db, chunk_id)

        return LineageResponse(
            chunk_id=lineage_data["chunk_id"],
            ancestors=[LineageNode(**ancestor) for ancestor in lineage_data["ancestors"]],
            descendants=[LineageNode(**descendant) for descendant in lineage_data["descendants"]],
            root_chunk_id=lineage_data["root_chunk_id"],
            total_generations=lineage_data["total_generations"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lineage: {str(e)}")


@router.get("/provenance/{chunk_id}", response_model=ProvenanceChain)
async def get_provenance(
    chunk_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get full provenance chain for a chunk."""
    try:
        lineage_data = await pipeline_service.get_lineage(db, chunk_id)

        # Combine ancestors + current chunk to get full chain
        all_nodes = lineage_data["ancestors"]

        # Get sessions and jobs from all nodes
        all_sessions = set()
        all_jobs = set()
        total_tokens = 0

        for node in all_nodes:
            all_sessions.update(node.get("session_ids", []))
            all_jobs.update(node.get("job_ids", []))
            total_tokens += node.get("total_tokens_used", 0)

        return ProvenanceChain(
            chunk_id=chunk_id,
            chain=[LineageNode(**node) for node in all_nodes],
            total_transformations=len(all_nodes),
            total_tokens_used=total_tokens,
            sessions=list(all_sessions),
            jobs=list(all_jobs)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provenance: {str(e)}")


# ============================================================================
# GRAPH VISUALIZATION
# ============================================================================

@router.get("/graph/chunk/{chunk_id}", response_model=TransformationGraph)
async def get_chunk_graph(
    chunk_id: UUID,
    include_content: bool = Query(False, description="Include full chunk content"),
    db: AsyncSession = Depends(get_db)
):
    """Get transformation graph for a specific chunk (all transformations from root)."""
    try:
        # First, get the root chunk ID for this chunk
        lineage_data = await pipeline_service.get_lineage(db, chunk_id)
        root_chunk_id = lineage_data["root_chunk_id"]

        graph = await pipeline_service.get_transformation_graph(
            db, root_chunk_id, include_content
        )

        return graph

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chunk graph: {str(e)}")


@router.post("/graph/session", response_model=List[TransformationGraph])
async def get_session_graph(
    request: SessionGraphRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get all transformation graphs for a session."""
    try:
        graphs = await pipeline_service.get_session_graph(
            db,
            request.session_id,
            include_content=request.include_content,
            max_generation=request.max_generation
        )

        return graphs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session graph: {str(e)}")


@router.post("/graph/collection", response_model=List[TransformationGraph])
async def get_collection_graph(
    request: CollectionGraphRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get all transformation graphs for a collection."""
    try:
        graphs = await pipeline_service.get_collection_graph(
            db,
            request.collection_id,
            include_content=request.include_content,
            max_generation=request.max_generation,
            filter_by_job_type=request.filter_by_job_type
        )

        return graphs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection graph: {str(e)}")


# ============================================================================
# RELATIONSHIPS
# ============================================================================

@router.get("/relationships/{chunk_id}")
async def get_relationships(
    chunk_id: UUID,
    relationship_types: Optional[List[str]] = Query(None),
    max_depth: int = Query(2, ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    """Get all relationships for a chunk."""
    try:
        from models.chunk_models import ChunkRelationship
        from sqlalchemy import select

        # Get direct relationships
        query = select(ChunkRelationship).where(
            (ChunkRelationship.source_chunk_id == chunk_id) |
            (ChunkRelationship.target_chunk_id == chunk_id)
        )

        if relationship_types:
            query = query.where(ChunkRelationship.relationship_type.in_(relationship_types))

        result = await db.execute(query)
        relationships = result.scalars().all()

        return {
            "chunk_id": chunk_id,
            "relationships": [r.to_dict() for r in relationships],
            "total": len(relationships)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    try:
        from models.pipeline_models import TransformationJob
        from sqlalchemy import select, func

        # Count jobs
        result = await db.execute(select(func.count()).select_from(TransformationJob))
        total_jobs = result.scalar_one()

        # Count active jobs
        result = await db.execute(
            select(func.count())
            .select_from(TransformationJob)
            .where(TransformationJob.status == JobStatus.PROCESSING)
        )
        active_jobs = result.scalar_one()

        return {
            "status": "healthy",
            "service": "transformation_pipeline",
            "total_jobs": total_jobs,
            "active_jobs": active_jobs
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
