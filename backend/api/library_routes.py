"""
Library API Routes

Endpoints for browsing imported collections, messages, and chunks in a hierarchical view.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from sqlalchemy.orm import selectinload
from pathlib import Path
import os

from database.connection import get_db
from models.chunk_models import Collection, Message, Chunk, Media
from models.pipeline_models import TransformationJob, ChunkTransformation, TransformationLineage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/library", tags=["library"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class CollectionSummary(BaseModel):
    """Summary of a collection for library browsing."""
    id: str
    title: str
    description: Optional[str]
    collection_type: str
    source_platform: Optional[str]
    message_count: int
    chunk_count: int
    media_count: int
    total_tokens: int
    word_count: int
    created_at: str
    original_date: Optional[str]  # From metadata.create_time or import_date
    import_date: Optional[str]
    metadata: dict


class MessageSummary(BaseModel):
    """Summary of a message for library browsing."""
    id: str
    collection_id: str
    sequence_number: int
    role: str
    message_type: Optional[str]
    summary: Optional[str]  # First 200 chars of content
    chunk_count: int
    token_count: int
    media_count: int
    timestamp: Optional[str]
    created_at: str
    metadata: dict


class ChunkDetail(BaseModel):
    """Detailed chunk information."""
    id: str
    message_id: str
    content: str
    chunk_level: str
    chunk_sequence: int
    token_count: Optional[int]
    is_summary: bool
    has_embedding: bool
    created_at: str


class MediaDetail(BaseModel):
    """Media file information."""
    id: str
    collection_id: str
    message_id: Optional[str]
    media_type: str
    mime_type: Optional[str]
    original_filename: Optional[str]
    size_bytes: Optional[int]
    is_archived: bool
    storage_path: Optional[str]


class TransformationSummary(BaseModel):
    """Summary of a transformation job for library browsing."""
    id: str
    name: str
    description: Optional[str]
    job_type: str
    status: str
    created_at: str
    completed_at: Optional[str]
    total_items: int
    processed_items: int
    progress_percentage: float
    tokens_used: int
    configuration: dict
    source_message_id: Optional[str]  # Extracted from configuration
    source_collection_id: Optional[str]  # Extracted from configuration


class TransformationDetail(BaseModel):
    """Detailed view of a transformation job with source and results."""
    job: TransformationSummary
    source_message: Optional[MessageSummary]
    source_collection: Optional[CollectionSummary]
    transformations: List[dict]  # ChunkTransformation details
    lineage: List[dict]  # Lineage information


class CollectionHierarchy(BaseModel):
    """Full hierarchical view of a collection."""
    collection: CollectionSummary
    messages: List[MessageSummary]
    recent_chunks: List[ChunkDetail]  # Sample chunks
    media: List[MediaDetail]


# ============================================================================
# COLLECTION ENDPOINTS
# ============================================================================

@router.get("/collections", response_model=List[CollectionSummary])
async def list_collections(
    source_platform: Optional[str] = None,
    collection_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all collections with filtering options.

    Args:
        source_platform: Filter by platform (e.g., 'chatgpt', 'claude')
        collection_type: Filter by type (e.g., 'conversation', 'session')
        search: Search in title and description
        limit: Maximum results (max 200)
        offset: Pagination offset
        db: Database session

    Returns:
        List of collection summaries
    """
    query = select(Collection).order_by(desc(Collection.created_at))

    # Apply filters
    if source_platform:
        query = query.where(Collection.source_platform == source_platform)

    if collection_type:
        query = query.where(Collection.collection_type == collection_type)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Collection.title.ilike(search_pattern)) |
            (Collection.description.ilike(search_pattern))
        )

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    collections = result.scalars().all()

    summaries = []
    for col in collections:
        # Extract original date from metadata if available (Unix timestamp)
        original_date = None
        metadata = col.extra_metadata or {}
        if 'create_time' in metadata and metadata['create_time']:
            try:
                from datetime import datetime
                original_date = datetime.fromtimestamp(metadata['create_time']).isoformat()
            except (ValueError, TypeError):
                # Fallback to import_date if conversion fails
                original_date = col.import_date.isoformat() if col.import_date else None
        else:
            # Use import_date as fallback
            original_date = col.import_date.isoformat() if col.import_date else None

        # Calculate word count from chunks
        word_count_query = await db.execute(
            select(func.sum(func.array_length(func.string_to_array(Chunk.content, ' '), 1)))
            .where(Chunk.collection_id == col.id)
        )
        word_count = word_count_query.scalar() or 0

        summaries.append(CollectionSummary(
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
        ))

    return summaries


@router.get("/collections/{collection_id}", response_model=CollectionHierarchy)
async def get_collection_hierarchy(
    collection_id: str,
    include_chunks: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Get hierarchical view of a collection with its messages.

    Args:
        collection_id: Collection UUID
        include_chunks: Whether to include chunk samples
        db: Database session

    Returns:
        Full collection hierarchy
    """
    try:
        col_uuid = UUID(collection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection ID format")

    # Get collection
    result = await db.execute(
        select(Collection).where(Collection.id == col_uuid)
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Get messages with their first chunk for summary
    messages_query = select(Message).where(
        Message.collection_id == col_uuid
    ).order_by(Message.sequence_number)

    messages_result = await db.execute(messages_query)
    messages = messages_result.scalars().all()

    message_summaries = []
    for msg in messages:
        # Get first chunk content for preview
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

        message_summaries.append(MessageSummary(
            id=str(msg.id),
            collection_id=str(msg.collection_id),
            sequence_number=msg.sequence_number,
            role=msg.role,
            message_type=msg.message_type,
            summary=summary_text,
            chunk_count=msg.chunk_count,
            token_count=msg.token_count,
            media_count=msg.media_count,
            timestamp=msg.timestamp.isoformat() if msg.timestamp else None,
            created_at=msg.created_at.isoformat(),
            metadata=msg.extra_metadata or {}
        ))

    # Get recent chunks (sample)
    recent_chunks = []
    if include_chunks:
        chunks_query = select(Chunk).where(
            Chunk.collection_id == col_uuid
        ).order_by(desc(Chunk.created_at)).limit(10)

        chunks_result = await db.execute(chunks_query)
        chunks = chunks_result.scalars().all()

        recent_chunks = [
            ChunkDetail(
                id=str(chunk.id),
                message_id=str(chunk.message_id),
                content=chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content,
                chunk_level=chunk.chunk_level,
                chunk_sequence=chunk.chunk_sequence,
                token_count=chunk.token_count,
                is_summary=chunk.is_summary,
                has_embedding=chunk.embedding is not None,
                created_at=chunk.created_at.isoformat()
            )
            for chunk in chunks
        ]

    # Get media
    media_query = select(Media).where(Media.collection_id == col_uuid)
    media_result = await db.execute(media_query)
    media_files = media_result.scalars().all()

    media_list = [
        MediaDetail(
            id=str(m.id),
            collection_id=str(m.collection_id),
            message_id=str(m.message_id) if m.message_id else None,
            media_type=m.media_type,
            mime_type=m.mime_type,
            original_filename=m.original_filename,
            size_bytes=m.size_bytes,
            is_archived=m.is_archived,
            storage_path=m.storage_path
        )
        for m in media_files
    ]

    # Extract original date from metadata
    metadata = collection.extra_metadata or {}
    original_date = None
    if 'create_time' in metadata and metadata['create_time']:
        try:
            from datetime import datetime
            original_date = datetime.fromtimestamp(metadata['create_time']).isoformat()
        except (ValueError, TypeError):
            original_date = collection.import_date.isoformat() if collection.import_date else None
    else:
        original_date = collection.import_date.isoformat() if collection.import_date else None

    # Calculate word count from chunks
    word_count_query = await db.execute(
        select(func.sum(func.array_length(func.string_to_array(Chunk.content, ' '), 1)))
        .where(Chunk.collection_id == col_uuid)
    )
    word_count = word_count_query.scalar() or 0

    return CollectionHierarchy(
        collection=CollectionSummary(
            id=str(collection.id),
            title=collection.title,
            description=collection.description,
            collection_type=collection.collection_type,
            source_platform=collection.source_platform,
            message_count=collection.message_count,
            chunk_count=collection.chunk_count,
            media_count=collection.media_count,
            total_tokens=collection.total_tokens or 0,
            word_count=word_count,
            created_at=collection.created_at.isoformat(),
            original_date=original_date,
            import_date=collection.import_date.isoformat() if collection.import_date else None,
            metadata=metadata
        ),
        messages=message_summaries,
        recent_chunks=recent_chunks,
        media=media_list
    )


# ============================================================================
# MESSAGE ENDPOINTS
# ============================================================================

@router.get("/messages/{message_id}/chunks", response_model=List[ChunkDetail])
async def get_message_chunks(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chunks for a specific message.

    Args:
        message_id: Message UUID
        db: Database session

    Returns:
        List of chunks in sequence order
    """
    try:
        msg_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    # Verify message exists
    msg_result = await db.execute(select(Message).where(Message.id == msg_uuid))
    message = msg_result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get chunks
    chunks_query = select(Chunk).where(
        Chunk.message_id == msg_uuid
    ).order_by(Chunk.chunk_sequence)

    chunks_result = await db.execute(chunks_query)
    chunks = chunks_result.scalars().all()

    return [
        ChunkDetail(
            id=str(chunk.id),
            message_id=str(chunk.message_id),
            content=chunk.content,
            chunk_level=chunk.chunk_level,
            chunk_sequence=chunk.chunk_sequence,
            token_count=chunk.token_count,
            is_summary=chunk.is_summary,
            has_embedding=chunk.embedding is not None,
            created_at=chunk.created_at.isoformat()
        )
        for chunk in chunks
    ]


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@router.get("/search", response_model=dict)
async def search_library(
    query: str = Query(..., min_length=2),
    search_type: str = Query("all", regex="^(all|collections|messages|chunks)$"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search across the library.

    Args:
        query: Search query string
        search_type: What to search (all, collections, messages, chunks)
        limit: Maximum results
        db: Database session

    Returns:
        Search results grouped by type
    """
    search_pattern = f"%{query}%"
    results = {
        "query": query,
        "collections": [],
        "messages": [],
        "chunks": []
    }

    # Search collections
    if search_type in ("all", "collections"):
        col_query = select(Collection).where(
            (Collection.title.ilike(search_pattern)) |
            (Collection.description.ilike(search_pattern))
        ).limit(limit)

        col_result = await db.execute(col_query)
        collections = col_result.scalars().all()

        results["collections"] = [
            {
                "id": str(col.id),
                "title": col.title,
                "type": col.collection_type,
                "platform": col.source_platform
            }
            for col in collections
        ]

    # Search chunks (content)
    if search_type in ("all", "chunks"):
        chunk_query = select(Chunk).where(
            Chunk.content.ilike(search_pattern)
        ).limit(limit)

        chunk_result = await db.execute(chunk_query)
        chunks = chunk_result.scalars().all()

        results["chunks"] = [
            {
                "id": str(chunk.id),
                "message_id": str(chunk.message_id),
                "collection_id": str(chunk.collection_id),
                "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
            }
            for chunk in chunks
        ]

    return results


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats", response_model=dict)
async def get_library_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overall library statistics.

    Returns:
        Statistics about imported content
    """
    # Count collections
    col_count = await db.execute(select(func.count(Collection.id)))
    collection_count = col_count.scalar()

    # Count messages
    msg_count = await db.execute(select(func.count(Message.id)))
    message_count = msg_count.scalar()

    # Count chunks
    chunk_count_query = await db.execute(select(func.count(Chunk.id)))
    chunk_count = chunk_count_query.scalar()

    # Count chunks with embeddings
    embedded_count = await db.execute(
        select(func.count(Chunk.id)).where(Chunk.embedding.is_not(None))
    )
    embedded_chunks = embedded_count.scalar()

    # Count media
    media_count_query = await db.execute(select(func.count(Media.id)))
    media_count = media_count_query.scalar()

    # Group by platform
    platform_stats = await db.execute(
        select(
            Collection.source_platform,
            func.count(Collection.id).label('count')
        ).group_by(Collection.source_platform)
    )

    platforms = {row[0] or 'unknown': row[1] for row in platform_stats}

    return {
        "collections": collection_count,
        "messages": message_count,
        "chunks": chunk_count,
        "chunks_with_embeddings": embedded_chunks,
        "embedding_coverage": (embedded_chunks / chunk_count * 100) if chunk_count > 0 else 0,
        "media_files": media_count,
        "platforms": platforms
    }


@router.get("/media")
async def list_media(
    collection_id: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all media files, optionally filtered by collection.

    Args:
        collection_id: Optional collection ID to filter by
        limit: Maximum number of results (default 100, max 500)
        offset: Number of results to skip
        db: Database session

    Returns:
        List of media records with metadata
    """
    query = select(Media).order_by(Media.created_at.desc())

    # Filter by collection if provided
    if collection_id:
        query = query.where(Media.collection_id == collection_id)

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    media_records = result.scalars().all()

    # Convert to response format
    media_list = []
    for media in media_records:
        media_list.append({
            "id": media.original_media_id,
            "filename": media.original_filename,
            "mime_type": media.mime_type,
            "storage_path": media.storage_path,
            "collection_id": str(media.collection_id),
            "message_id": str(media.message_id) if media.message_id else None,
            "created_at": media.created_at.isoformat() if media.created_at else None,
            "custom_metadata": media.extra_metadata or {}
        })

    return {"media": media_list, "count": len(media_list)}


@router.get("/media/{media_id}/metadata")
async def get_media_metadata(
    media_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed metadata for a media file including conversation and transformation links.

    Args:
        media_id: Original media ID
        db: Database session

    Returns:
        Detailed metadata including:
        - Basic file info
        - Conversation and message links
        - Transformations that reference this media
        - EXIF/custom metadata
    """
    from models.pipeline_models import TransformationJob

    # Get media record
    result = await db.execute(
        select(Media).where(Media.original_media_id == media_id)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    metadata = {
        "id": media.original_media_id,
        "filename": media.original_filename,
        "mime_type": media.mime_type,
        "storage_path": media.storage_path,
        "created_at": media.created_at.isoformat() if media.created_at else None,
        "custom_metadata": media.extra_metadata or {},
        "conversation": None,
        "message": None,
        "transformations": []
    }

    # Get conversation info
    if media.collection_id:
        conv_result = await db.execute(
            select(Collection).where(Collection.id == media.collection_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if conversation:
            metadata["conversation"] = {
                "id": str(conversation.id),
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "source_platform": conversation.source_platform
            }

    # Get message info
    if media.message_id:
        msg_result = await db.execute(
            select(Message).where(Message.id == media.message_id)
        )
        message = msg_result.scalar_one_or_none()
        if message:
            # Get message content from chunks
            chunks_result = await db.execute(
                select(Chunk.content).where(Chunk.message_id == message.id).limit(1)
            )
            first_chunk = chunks_result.scalar_one_or_none()

            metadata["message"] = {
                "id": str(message.id),
                "role": message.role,
                "content": first_chunk[:500] if first_chunk else None,  # First 500 chars
                "created_at": message.created_at.isoformat() if message.created_at else None
            }

    # TODO: Find transformations that reference this media
    # For now, transformations list is empty
    # Will be implemented when transformation linkage is established

    return metadata


@router.get("/media/{media_id}/file")
async def get_media_file(
    media_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Serve a media file by original ID.

    Supports ChatGPT file IDs (file-XXX format).
    Returns 404 with specific message if file is a placeholder (not found in archive).

    Args:
        media_id: Original media ID (e.g., "file-BTGHeayl9isKTp9kvyBzirg0")
        db: Database session

    Returns:
        File response with the media content
    """
    import mimetypes

    # First check database for media record
    result = await db.execute(
        select(Media).where(Media.original_media_id == media_id)
    )
    media_record = result.scalar_one_or_none()

    if media_record:
        # Check if this is a placeholder (file not found in archive)
        metadata = media_record.extra_metadata or {}
        if not media_record.storage_path or metadata.get('missing_from_archive'):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "file_not_in_archive",
                    "message": f"Media file '{media_record.original_filename}' was referenced but not found in archive",
                    "media_id": media_id,
                    "can_upload": True
                }
            )

        # File should exist at storage_path
        file_path = Path(media_record.storage_path)
        if file_path.exists():
            mime_type = media_record.mime_type or "application/octet-stream"

            # For images, serve inline (display in browser) not as download
            from fastapi.responses import Response
            with open(file_path, 'rb') as f:
                content = f.read()

            headers = {}
            if mime_type.startswith('image/'):
                # inline = display in browser, attachment = force download
                headers['Content-Disposition'] = 'inline'
            else:
                # Non-images: suggest filename for download
                headers['Content-Disposition'] = f'attachment; filename="{media_record.original_filename}"'

            return Response(
                content=content,
                media_type=mime_type,
                headers=headers
            )

    # Fallback: Search filesystem (for backwards compatibility)
    backend_dir = Path(__file__).parent.parent
    media_base_dir = backend_dir / "media" / "chatgpt"

    if media_base_dir.exists():
        # Search for file by ID in all subdirectories
        # Files are now stored as {media_id}.ext
        for root, dirs, files in os.walk(media_base_dir):
            for filename in files:
                # Match if filename starts with media_id
                if filename.startswith(media_id):
                    file_path = Path(root) / filename
                    if file_path.exists():
                        mime_type, _ = mimetypes.guess_type(str(file_path))
                        if not mime_type:
                            mime_type = "application/octet-stream"

                        # Serve images inline for browser display
                        from fastapi.responses import Response
                        with open(file_path, 'rb') as f:
                            content = f.read()

                        headers = {}
                        if mime_type.startswith('image/'):
                            headers['Content-Disposition'] = 'inline'
                        else:
                            headers['Content-Disposition'] = f'attachment; filename="{filename}"'

                        return Response(
                            content=content,
                            media_type=mime_type,
                            headers=headers
                        )

    # Not found anywhere
    logger.error(f"Media file not found for ID: {media_id}")
    raise HTTPException(
        status_code=404,
        detail=f"Media file not found: {media_id}"
    )


# ============================================================================
# TRANSFORMATION LIBRARY ENDPOINTS
# ============================================================================

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
