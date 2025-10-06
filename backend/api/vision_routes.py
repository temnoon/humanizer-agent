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
from services.image_metadata import ImageMetadataExtractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vision", tags=["vision"])

# Initialize metadata extractor
metadata_extractor = ImageMetadataExtractor()


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

        # Extract metadata using PIL/Pillow
        image_metadata = metadata_extractor.extract_all_metadata(str(storage_path))

        # Get dimensions
        dimensions = image_metadata.get("dimensions", {})
        width = dimensions.get("width")
        height = dimensions.get("height")

        # Build extra_metadata with all extracted data
        extra_metadata = {
            "uploaded_by": user_id,
            "format": image_metadata.get("format"),
            "mode": image_metadata.get("mode"),
            "exif": image_metadata.get("exif", {}),
            "ai_metadata": image_metadata.get("ai_metadata", {}),
            "created_date": image_metadata.get("created_date"),
            "camera": image_metadata.get("camera")
        }

        # Extract prompt if present
        ai_meta = image_metadata.get("ai_metadata", {})
        prompt = ai_meta.get("prompt")
        generator = ai_meta.get("generator")

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
            platform=generator or "upload",  # Use generator if detected, else "upload"
            extra_metadata=extra_metadata
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
            "content_type": file.content_type,
            "width": width,
            "height": height,
            "prompt": prompt,  # AI generation prompt if detected
            "generator": generator,  # AI generator if detected
            "has_metadata": len(extra_metadata.get("exif", {})) > 0
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload-bulk", status_code=201)
async def upload_bulk_images(
    files: list[UploadFile] = File(...),
    user_id: str = Form(...),
    collection_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload multiple images at once (folder import support).

    Args:
        files: List of image files
        user_id: User ID
        collection_id: Optional collection to link all images to
        db: Database session

    Returns:
        {
            "uploaded": [...],
            "failed": [...],
            "total": int,
            "success_count": int,
            "fail_count": int
        }
    """
    results = {"uploaded": [], "failed": [], "total": len(files), "success_count": 0, "fail_count": 0}

    for file in files:
        try:
            # Call single upload logic (reuse the upload endpoint logic)
            # For now, process inline
            file_id = f"file-{uuid4().hex[:24]}"
            ext_map = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/jpg': '.jpg', 'image/webp': '.webp', 'image/gif': '.gif'}
            ext = ext_map.get(file.content_type, '.png')

            upload_dir = Path("backend/media/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            storage_path = upload_dir / f"{file_id}{ext}"

            with open(storage_path, 'wb') as f:
                shutil.copyfileobj(file.file, f)

            file_size = storage_path.stat().st_size
            image_metadata = metadata_extractor.extract_all_metadata(str(storage_path))
            dimensions = image_metadata.get("dimensions", {})
            width, height = dimensions.get("width"), dimensions.get("height")

            extra_metadata = {
                "uploaded_by": user_id,
                "format": image_metadata.get("format"),
                "ai_metadata": image_metadata.get("ai_metadata", {}),
                "exif": image_metadata.get("exif", {})
            }

            ai_meta = image_metadata.get("ai_metadata", {})
            prompt = ai_meta.get("prompt")
            generator = ai_meta.get("generator")

            media = Media(
                id=uuid4(), original_media_id=file_id, storage_path=str(storage_path),
                mime_type=file.content_type, file_size_bytes=file_size,
                original_filename=file.filename, width=width, height=height,
                platform=generator or "upload", extra_metadata=extra_metadata
            )
            db.add(media)

            chunk_content = {"content_type": "image_asset_pointer", "asset_pointer": f"file-service://{file_id}", "size_bytes": file_size, "width": width, "height": height}
            chunk = Chunk(id=uuid4(), collection_id=UUID(collection_id) if collection_id else None, chunk_type="image", content=str(chunk_content), chunk_sequence=0)
            db.add(chunk)

            await db.commit()

            results["uploaded"].append({"media_id": file_id, "filename": file.filename, "prompt": prompt, "generator": generator})
            results["success_count"] += 1

        except Exception as e:
            results["failed"].append({"filename": file.filename, "error": str(e)})
            results["fail_count"] += 1
            logger.error(f"Failed to upload {file.filename}: {e}")

    return results


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

# ============================================================================
# APPLE PHOTOS INTEGRATION (macOS only)
# ============================================================================

@router.get("/apple-photos/available")
async def check_apple_photos_available():
    """Check if Apple Photos is available on this system"""
    from services.apple_photos_service import ApplePhotosService

    service = ApplePhotosService()
    is_available = service.is_available()

    return {
        "available": is_available,
        "platform": service.is_macos,
        "message": "Apple Photos is available" if is_available else "Apple Photos not available (macOS only)"
    }


@router.get("/apple-photos/albums")
async def get_apple_photos_albums():
    """Get list of albums from Apple Photos library"""
    from services.apple_photos_service import ApplePhotosService

    service = ApplePhotosService()

    if not service.is_available():
        raise HTTPException(
            status_code=400,
            detail="Apple Photos not available on this system"
        )

    try:
        albums = service.get_albums()
        photo_count = service.get_photo_count()

        return {
            "albums": albums,
            "total_photos": photo_count
        }
    except Exception as e:
        logger.error(f"Failed to get albums: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apple-photos/export-album")
async def export_apple_photos_album(
    album_name: str,
    export_path: str,
    limit: Optional[int] = None
):
    """
    Export photos from an Apple Photos album to a folder

    Args:
        album_name: Name of the album to export
        export_path: Path to export photos to
        limit: Maximum number of photos to export (optional)

    Returns:
        Export status and stats
    """
    from services.apple_photos_service import ApplePhotosService

    service = ApplePhotosService()

    if not service.is_available():
        raise HTTPException(
            status_code=400,
            detail="Apple Photos not available on this system"
        )

    try:
        result = service.export_album(album_name, export_path, limit)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export album: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apple-photos/export-recent")
async def export_recent_apple_photos(
    export_path: str,
    days: int = 30,
    limit: int = 100
):
    """
    Export recent photos from Apple Photos library

    Args:
        export_path: Path to export photos to
        days: Number of days back to search (default: 30)
        limit: Maximum number of photos to export (default: 100)

    Returns:
        Export status and stats
    """
    from services.apple_photos_service import ApplePhotosService

    service = ApplePhotosService()

    if not service.is_available():
        raise HTTPException(
            status_code=400,
            detail="Apple Photos not available on this system"
        )

    try:
        result = service.export_recent(export_path, days, limit)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export recent photos: {e}")
        raise HTTPException(status_code=500, detail=str(e))
