"""
Library Transformations API

Endpoints for browsing and managing transformation jobs.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from database.connection import get_db
from models.chunk_models import Collection, Message, Chunk
from models.pipeline_models import TransformationJob, ChunkTransformation, TransformationLineage
from .library_schemas import (
    TransformationSummary,
    TransformationDetail,
    MessageSummary,
    CollectionSummary
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/transformations", response_model=List[TransformationSummary])
async def list_transformations(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all transformation jobs (completed transformations library).

    Args:
        status: Filter by status (completed, failed, etc.)
        job_type: Filter by job type (persona_transform, madhyamaka_detect, etc.)
        search: Search in name and description
        limit: Maximum results (max 200)
        offset: Pagination offset
        db: Database session

    Returns:
        List of transformation job summaries
    """
    query = select(TransformationJob).order_by(desc(TransformationJob.created_at))

    # Apply filters
    if status:
        query = query.where(TransformationJob.status == status)

    if job_type:
        query = query.where(TransformationJob.job_type == job_type)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (TransformationJob.name.ilike(search_pattern)) |
            (TransformationJob.description.ilike(search_pattern))
        )

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    jobs = result.scalars().all()

    summaries = []
    for job in jobs:
        # Extract source references from configuration
        config = job.configuration or {}
        source_message_id = None
        source_collection_id = None

        if 'source_message_ids' in config and config['source_message_ids']:
            source_message_id = str(config['source_message_ids'][0])

        if 'source_collection_id' in config:
            source_collection_id = str(config['source_collection_id'])

        summaries.append(TransformationSummary(
            id=str(job.id),
            name=job.name,
            description=job.description,
            job_type=job.job_type,
            status=job.status,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            total_items=job.total_items,
            processed_items=job.processed_items,
            progress_percentage=job.progress_percentage,
            tokens_used=job.tokens_used,
            configuration=config,
            source_message_id=source_message_id,
            source_collection_id=source_collection_id
        ))

    return summaries


@router.get("/transformations/{job_id}", response_model=TransformationDetail)
async def get_transformation_detail(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed view of a transformation job with source and result links.

    Args:
        job_id: Transformation job UUID
        db: Database session

    Returns:
        Full transformation details including source message, collection, and results
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    # Get job
    result = await db.execute(
        select(TransformationJob).where(TransformationJob.id == job_uuid)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Transformation job not found")

    # Extract source references from configuration
    config = job.configuration or {}
    source_message_id = None
    source_collection_id = None

    if 'source_message_ids' in config and config['source_message_ids']:
        source_message_id = str(config['source_message_ids'][0])

    if 'source_collection_id' in config:
        source_collection_id = str(config['source_collection_id'])

    # Create job summary
    job_summary = TransformationSummary(
        id=str(job.id),
        name=job.name,
        description=job.description,
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        total_items=job.total_items,
        processed_items=job.processed_items,
        progress_percentage=job.progress_percentage,
        tokens_used=job.tokens_used,
        configuration=config,
        source_message_id=source_message_id,
        source_collection_id=source_collection_id
    )

    # Get source message if available
    source_message = None
    if source_message_id:
        try:
            msg_uuid = UUID(source_message_id)
            msg_result = await db.execute(
                select(Message).where(Message.id == msg_uuid)
            )
            msg = msg_result.scalar_one_or_none()

            if msg:
                # Get first chunk for preview
                chunk_query = select(Chunk).where(
                    and_(
                        Chunk.message_id == msg.id,
                        Chunk.chunk_sequence == 0
                    )
                ).limit(1)

                chunk_result = await db.execute(chunk_query)
                first_chunk = chunk_result.scalar_one_or_none()

                summary_text = None
                if first_chunk:
                    summary_text = first_chunk.content[:200] + "..." if len(first_chunk.content) > 200 else first_chunk.content

                source_message = MessageSummary(
                    id=str(msg.id),
                    collection_id=str(msg.collection_id),
                    sequence_number=msg.sequence_number,
                    role=msg.role,
                    message_type=msg.message_type,
                    summary=summary_text,
                    chunk_count=msg.chunk_count,
                    token_count=msg.token_count or 0,
                    media_count=msg.media_count,
                    timestamp=msg.timestamp.isoformat() if msg.timestamp else None,
                    created_at=msg.created_at.isoformat(),
                    metadata=msg.extra_metadata or {}
                )
        except ValueError:
            pass

    # Get source collection if available
    source_collection = None
    if source_collection_id:
        try:
            col_uuid = UUID(source_collection_id)
            col_result = await db.execute(
                select(Collection).where(Collection.id == col_uuid)
            )
            col = col_result.scalar_one_or_none()

            if col:
                metadata = col.extra_metadata or {}
                original_date = None
                if 'create_time' in metadata and metadata['create_time']:
                    try:
                        from datetime import datetime
                        original_date = datetime.fromtimestamp(metadata['create_time']).isoformat()
                    except (ValueError, TypeError):
                        original_date = col.import_date.isoformat() if col.import_date else None
                else:
                    original_date = col.import_date.isoformat() if col.import_date else None

                word_count_query = await db.execute(
                    select(func.sum(func.array_length(func.string_to_array(Chunk.content, ' '), 1)))
                    .where(Chunk.collection_id == col.id)
                )
                word_count = word_count_query.scalar() or 0

                source_collection = CollectionSummary(
                    id=str(col.id),
                    title=col.title,
                    description=col.description,
                    collection_type=col.collection_type,
                    source_platform=col.source_platform,
                    message_count=col.message_count,
                    chunk_count=col.chunk_count,
                    media_count=col.media_count,
                    total_tokens=col.total_tokens or 0,
                    word_count=word_count,
                    created_at=col.created_at.isoformat(),
                    original_date=original_date,
                    import_date=col.import_date.isoformat() if col.import_date else None,
                    metadata=metadata
                )
        except ValueError:
            pass

    # Get chunk transformations
    trans_result = await db.execute(
        select(ChunkTransformation)
        .where(ChunkTransformation.job_id == job_uuid)
        .order_by(ChunkTransformation.sequence_number)
    )
    chunk_transformations = trans_result.scalars().all()

    transformations = [ct.to_dict() for ct in chunk_transformations]

    # Get lineage if available
    # Note: PostgreSQL ARRAY.any() requires the value to be in the array
    lineage_result = await db.execute(
        select(TransformationLineage)
        .where(TransformationLineage.job_ids.any(job_uuid))
        .order_by(TransformationLineage.generation)
    )
    lineage_records = lineage_result.scalars().all()

    lineage = [lr.to_dict() for lr in lineage_records]

    return TransformationDetail(
        job=job_summary,
        source_message=source_message,
        source_collection=source_collection,
        transformations=transformations,
        lineage=lineage
    )


@router.post("/transformations/{job_id}/reapply")
async def reapply_transformation(
    job_id: str,
    target_message_id: str = Query(..., description="Message ID to apply transformation to"),
    db: AsyncSession = Depends(get_db)
):
    """
    Reapply a transformation to new content.

    Args:
        job_id: Source transformation job UUID
        target_message_id: Target message to transform
        db: Database session

    Returns:
        New transformation job ID
    """
    try:
        job_uuid = UUID(job_id)
        target_uuid = UUID(target_message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Get source job
    result = await db.execute(
        select(TransformationJob).where(TransformationJob.id == job_uuid)
    )
    source_job = result.scalar_one_or_none()

    if not source_job:
        raise HTTPException(status_code=404, detail="Source transformation job not found")

    # Get target message
    msg_result = await db.execute(
        select(Message).where(Message.id == target_uuid)
    )
    target_message = msg_result.scalar_one_or_none()

    if not target_message:
        raise HTTPException(status_code=404, detail="Target message not found")

    # Get chunks for target message
    chunks_result = await db.execute(
        select(Chunk.id).where(Chunk.message_id == target_uuid)
    )
    chunk_ids = [str(c) for c in chunks_result.scalars().all()]

    if not chunk_ids:
        raise HTTPException(status_code=400, detail="Target message has no chunks")

    # Create new job with same configuration but new target
    new_config = source_job.configuration.copy()
    new_config['source_message_ids'] = [str(target_uuid)]
    new_config['source_chunk_ids'] = chunk_ids
    new_config['source_collection_id'] = str(target_message.collection_id)

    new_job = TransformationJob(
        user_id=source_job.user_id,
        session_id=source_job.session_id,
        name=f"{source_job.name} (reapplied)",
        description=f"Reapplied from job {job_id}",
        job_type=source_job.job_type,
        status="pending",
        total_items=len(chunk_ids),
        configuration=new_config,
        priority=source_job.priority,
        extra_metadata={
            "reapplied_from": str(job_id),
            "original_job_name": source_job.name
        }
    )

    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    return {
        "job_id": str(new_job.id),
        "status": "pending",
        "message": f"Transformation queued for processing"
    }
