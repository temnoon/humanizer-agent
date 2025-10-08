"""
Library Collections API

Endpoints for browsing collections and messages.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from database.connection import get_db
from models.chunk_models import Collection, Message, Chunk, Media
from .library_schemas import (
    CollectionSummary,
    MessageSummary,
    ChunkDetail,
    MediaDetail,
    CollectionHierarchy
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/collections", response_model=List[CollectionSummary])
async def list_collections(
    source_platform: Optional[str] = None,
    collection_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=5000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all collections with filtering options.

    Args:
        source_platform: Filter by platform (e.g., 'chatgpt', 'claude')
        collection_type: Filter by type (e.g., 'conversation', 'session')
        search: Search in title and description
        limit: Maximum results (max 5000, configurable from frontend)
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
