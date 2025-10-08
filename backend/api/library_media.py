"""
Library Media, Search & Stats API

Endpoints for media files, search functionality, and library statistics.
"""

import logging
import os
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.connection import get_db
from models.chunk_models import Collection, Message, Chunk, Media

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", response_model=dict)
async def search_library(
    query: str = Query(..., min_length=2),
    search_type: str = Query("all", pattern="^(all|collections|messages|chunks)$"),
    limit: int = Query(20, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Search across the library.

    Args:
        query: Search query string
        search_type: What to search (all, collections, messages, chunks)
        limit: Maximum results (max 1000, configurable from frontend)
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
    search: Optional[str] = None,
    generator: Optional[str] = None,
    mime_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(100, le=10000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all media files with comprehensive filtering.

    Args:
        collection_id: Optional collection ID to filter by
        search: Search in filename or AI prompts
        generator: Filter by generator (dall-e, stable-diffusion, midjourney, etc.)
        mime_type: Filter by MIME type (image/png, image/jpeg, etc.)
        date_from: Filter by creation date (from) - ISO format YYYY-MM-DD
        date_to: Filter by creation date (to) - ISO format YYYY-MM-DD
        limit: Maximum number of results (default 100, max 10000)
        offset: Number of results to skip
        db: Database session

    Returns:
        List of media records with metadata and total count
    """
    from datetime import datetime

    # Build base query
    query = select(Media).order_by(Media.created_at.desc())
    count_query = select(func.count()).select_from(Media)

    # Filter by collection if provided
    if collection_id:
        query = query.where(Media.collection_id == collection_id)
        count_query = count_query.where(Media.collection_id == collection_id)

    # Search filter (filename or metadata)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Media.original_filename.ilike(search_pattern)) |
            (Media.extra_metadata['ai_prompt'].astext.ilike(search_pattern))
        )
        count_query = count_query.where(
            (Media.original_filename.ilike(search_pattern)) |
            (Media.extra_metadata['ai_prompt'].astext.ilike(search_pattern))
        )

    # Generator filter
    if generator:
        query = query.where(Media.extra_metadata['generator'].astext == generator)
        count_query = count_query.where(Media.extra_metadata['generator'].astext == generator)

    # MIME type filter
    if mime_type:
        query = query.where(Media.mime_type == mime_type)
        count_query = count_query.where(Media.mime_type == mime_type)

    # Date range filters
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.where(Media.created_at >= date_from_dt)
            count_query = count_query.where(Media.created_at >= date_from_dt)
        except ValueError:
            pass  # Ignore invalid date format

    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            # Add one day to include the entire end date
            from datetime import timedelta
            date_to_dt = date_to_dt + timedelta(days=1)
            query = query.where(Media.created_at < date_to_dt)
            count_query = count_query.where(Media.created_at < date_to_dt)
        except ValueError:
            pass  # Ignore invalid date format

    # Get total count
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    media_records = result.scalars().all()

    # Deduplicate by original_media_id (keep first occurrence)
    # This handles duplicate media records in the database
    seen_ids = set()
    unique_media = []
    for media in media_records:
        if media.original_media_id not in seen_ids:
            seen_ids.add(media.original_media_id)
            unique_media.append(media)

    # Convert to response format
    media_list = []
    for media in unique_media:
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

    return {
        "media": media_list,
        "count": len(media_list),
        "total": total_count,
        "offset": offset,
        "limit": limit
    }


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
    # Use first() to handle duplicates gracefully (there may be duplicate records with same original_media_id)
    result = await db.execute(
        select(Media).where(Media.original_media_id == media_id).limit(1)
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
            with open(file_path, 'rb') as f:
                content = f.read()

            headers = {}
            if mime_type.startswith('image/'):
                # inline = display in browser, attachment = force download
                headers['Content-Disposition'] = 'inline'
            else:
                # Non-images: suggest filename for download
                # Use RFC 2231 encoding for Unicode filenames
                from urllib.parse import quote
                filename_encoded = quote(media_record.original_filename)
                headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename_encoded}'

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
                        with open(file_path, 'rb') as f:
                            content = f.read()

                        headers = {}
                        if mime_type.startswith('image/'):
                            headers['Content-Disposition'] = 'inline'
                        else:
                            # Use RFC 2231 encoding for Unicode filenames
                            from urllib.parse import quote
                            filename_encoded = quote(filename)
                            headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename_encoded}'

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
