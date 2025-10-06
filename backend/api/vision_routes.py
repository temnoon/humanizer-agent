"""
Vision API Routes

Endpoints for image upload and Claude vision operations (OCR, analysis, description).
Integrates with transformation pipeline for background processing.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from models.chunk_models import Chunk, Media, Message
from models.pipeline_models import TransformationJob
from services.vision_service import VisionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vision", tags=["vision"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class VisionJobCreate(BaseModel):
    """Request model for creating vision job."""
    media_id: str
    job_type: str  # vision_ocr, vision_describe, vision_analyze, vision_diagram
    prompt: Optional[str] = None
    add_to_collection: bool = True


class VisionJobResponse(BaseModel):
    """Response model for vision job."""
    job_id: str
    status: str
    job_type: str
    media_id: str
    result_chunk_id: Optional[str] = None


# ============================================================================
# IMAGE UPLOAD
# ============================================================================

@router.post("/upload", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    collection_id: Optional[str] = Form(None),
    message_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an image file and create media + chunk records.

    Args:
        file: Image file (PNG, JPEG, WEBP, GIF)
        user_id: User ID
        collection_id: Optional collection to link
        message_id: Optional message to link
        db: Database session

    Returns:
        {
            "media_id": "...",
            "chunk_id": "...",
            "storage_path": "...",
            "thumbnail_url": "..."
        }

    Raises:
        HTTPException: If invalid file type or upload fails
    """
    # Validate file type
    allowed_types = {
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/webp',
        'image/gif'
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}"
        )

    try:
        # Generate file ID
        file_id = f"file-{uuid4().hex[:24]}"

        # Determine file extension
        ext_map = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/webp': '.webp',
            'image/gif': '.gif'
        }
        ext = ext_map.get(file.content_type, '.png')

        # Create storage path
        upload_dir = Path("backend/media/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        storage_path = upload_dir / f"{file_id}{ext}"

        # Save file
        with open(storage_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        # Get file size
        file_size = storage_path.stat().st_size

        # TODO: Extract image dimensions (requires PIL/Pillow)
        # For now, set to None
        width, height = None, None

        # Create media record
        media = Media(
            id=uuid4(),
            original_media_id=file_id,
            storage_path=str(storage_path),
            mime_type=file.content_type,
            file_size_bytes=file_size,
            original_filename=file.filename,
            width=width,
            height=height,
            platform="upload",
            extra_metadata={"uploaded_by": user_id}
        )
        db.add(media)

        # Create chunk with image_asset_pointer
        chunk_content = {
            "content_type": "image_asset_pointer",
            "asset_pointer": f"file-service://{file_id}",
            "size_bytes": file_size,
            "width": width,
            "height": height,
            "fovea": None,
            "metadata": {
                "original_filename": file.filename,
                "uploaded": True
            }
        }

        chunk = Chunk(
            id=uuid4(),
            collection_id=UUID(collection_id) if collection_id else None,
            message_id=UUID(message_id) if message_id else None,
            chunk_type="image",
            content=str(chunk_content),  # Store as JSON string
            chunk_sequence=0,
            embedding=None
        )
        db.add(chunk)

        await db.commit()
        await db.refresh(media)
        await db.refresh(chunk)

        logger.info(f"Uploaded image: {file_id}")

        return {
            "media_id": file_id,
            "chunk_id": str(chunk.id),
            "storage_path": str(storage_path),
            "thumbnail_url": f"/api/library/media/{file_id}",
            "file_size": file_size,
            "content_type": file.content_type
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# VISION JOB CREATION
# ============================================================================

@router.post("/jobs", status_code=201)
async def create_vision_job(
    job_request: VisionJobCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a vision processing job (OCR, description, analysis).

    Args:
        job_request: Job configuration
        db: Database session

    Returns:
        VisionJobResponse with job ID and status

    Raises:
        HTTPException: If media not found or invalid job type
    """
    # Validate job type
    valid_types = {
        'vision_ocr',
        'vision_describe',
        'vision_analyze',
        'vision_diagram'
    }

    if job_request.job_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job type: {job_request.job_type}. Valid: {valid_types}"
        )

    # Find media record
    result = await db.execute(
        select(Media).where(Media.original_media_id == job_request.media_id)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=404,
            detail=f"Media not found: {job_request.media_id}"
        )

    # Find source chunk (image chunk)
    result = await db.execute(
        select(Chunk).where(
            Chunk.chunk_type == "image",
            Chunk.content.contains(job_request.media_id)
        ).limit(1)
    )
    source_chunk = result.scalar_one_or_none()

    if not source_chunk:
        raise HTTPException(
            status_code=404,
            detail=f"Image chunk not found for media: {job_request.media_id}"
        )

    # Create transformation job
    job = TransformationJob(
        id=uuid4(),
        job_type=job_request.job_type,
        status="pending",
        source_chunk_id=source_chunk.id,
        parameters={
            "media_id": job_request.media_id,
            "prompt": job_request.prompt,
            "add_to_collection": job_request.add_to_collection
        },
        result_data={}
    )
    db.add(job)

    await db.commit()
    await db.refresh(job)

    logger.info(f"Created vision job: {job.id} ({job_request.job_type})")

    return VisionJobResponse(
        job_id=str(job.id),
        status=job.status,
        job_type=job.job_type,
        media_id=job_request.media_id,
        result_chunk_id=None
    )


# ============================================================================
# JOB STATUS & RESULTS
# ============================================================================

@router.get("/jobs/{job_id}")
async def get_vision_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get status and result of vision job.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        Job details including result if completed

    Raises:
        HTTPException: If job not found
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    result = await db.execute(
        select(TransformationJob).where(TransformationJob.id == job_uuid)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "id": str(job.id),
        "status": job.status,
        "job_type": job.job_type,
        "source_chunk_id": str(job.source_chunk_id) if job.source_chunk_id else None,
        "result_chunk_id": str(job.result_chunk_id) if job.result_chunk_id else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "error": job.error_message,
        "parameters": job.parameters or {}
    }

    # Include result data if completed
    if job.status == "completed" and job.result_data:
        response["result"] = job.result_data

    # Include result chunk content if available
    if job.result_chunk_id:
        result = await db.execute(
            select(Chunk).where(Chunk.id == job.result_chunk_id)
        )
        result_chunk = result.scalar_one_or_none()
        if result_chunk:
            response["result_content"] = result_chunk.content

    return response


# ============================================================================
# DIRECT VISION OPERATIONS (Synchronous)
# ============================================================================

@router.post("/ocr-direct")
async def ocr_direct(
    media_id: str = Query(...),
    prompt: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform OCR directly (synchronous, no job queue).

    Use for testing or immediate results.
    For production, use POST /jobs with job_type=vision_ocr.

    Args:
        media_id: Media file ID
        prompt: Custom OCR prompt
        db: Database session

    Returns:
        OCR result

    Raises:
        HTTPException: If media not found or OCR fails
    """
    from anthropic import Anthropic
    from config import get_settings

    settings = get_settings()

    # Find media
    result = await db.execute(
        select(Media).where(Media.original_media_id == media_id)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    if not media.storage_path:
        raise HTTPException(status_code=404, detail="Media file not found")

    # Initialize vision service
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    vision_service = VisionService(client)

    try:
        # Perform OCR
        result = await vision_service.ocr_image(
            image_path=media.storage_path,
            prompt=prompt
        )

        return result

    except Exception as e:
        logger.error(f"Direct OCR failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")
