"""
Archive Import API Routes

Endpoints for importing ChatGPT and other archives into the system.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database.connection import get_db
from models.db_models import User
from models.chunk_models import Collection
from services.chatgpt_importer import import_chatgpt_archive_task
from services.embedding_service import process_embeddings_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/import", tags=["import"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ImportChatGPTRequest(BaseModel):
    """Request to import ChatGPT archive."""
    archive_path: str = Field(..., description="Path to extracted ChatGPT archive folder")
    user_id: Optional[str] = Field(None, description="User ID (optional, defaults to anonymous)")
    generate_embeddings: bool = Field(True, description="Generate embeddings during import")


class ImportJobResponse(BaseModel):
    """Response for import job creation."""
    job_id: str
    status: str
    message: str


class ImportStatusResponse(BaseModel):
    """Response for import status check."""
    job_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: Optional[int] = None  # Percentage (0-100)
    current_item: Optional[str] = None
    total_items: Optional[int] = None
    stats: Optional[dict] = None
    error: Optional[str] = None


class ImportStatsResponse(BaseModel):
    """Import statistics response."""
    conversations_imported: int
    messages_imported: int
    chunks_created: int
    media_imported: int
    embeddings_queued: int
    errors: list


class ProcessEmbeddingsRequest(BaseModel):
    """Request to process embeddings."""
    max_chunks: Optional[int] = Field(None, description="Maximum number of chunks to process")


# ============================================================================
# IMPORT STATE MANAGEMENT
# ============================================================================

# In-memory job tracking (replace with Redis/database for production)
import_jobs: dict = {}


def create_job(job_type: str) -> str:
    """Create a new import job."""
    job_id = str(uuid4())
    import_jobs[job_id] = {
        'id': job_id,
        'type': job_type,
        'status': 'pending',
        'created_at': asyncio.get_event_loop().time(),
        'progress': 0,
        'total_items': 0,
        'current_item': None,
        'stats': None,
        'error': None
    }
    return job_id


def update_job(job_id: str, **kwargs):
    """Update job status."""
    if job_id in import_jobs:
        import_jobs[job_id].update(kwargs)


def get_job(job_id: str) -> Optional[dict]:
    """Get job status."""
    return import_jobs.get(job_id)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/chatgpt", response_model=ImportJobResponse)
async def import_chatgpt_archive(
    request: ImportChatGPTRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Import ChatGPT archive from a folder path.

    This endpoint starts a background task to import the archive.
    Use GET /api/import/jobs/{job_id} to check progress.

    Args:
        request: Import request with archive path
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Job ID for tracking import progress
    """
    archive_path = Path(request.archive_path)

    # Validate archive path
    if not archive_path.exists():
        raise HTTPException(status_code=400, detail=f"Archive path not found: {archive_path}")

    if not archive_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Archive path must be a directory: {archive_path}")

    conversations_file = archive_path / "conversations.json"
    if not conversations_file.exists():
        raise HTTPException(
            status_code=400,
            detail=f"conversations.json not found in archive: {archive_path}"
        )

    # Get or create user
    user_id = None
    if request.user_id:
        try:
            user_uuid = UUID(request.user_id)
            result = await db.execute(select(User).where(User.id == user_uuid))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail=f"User not found: {request.user_id}")
            user_id = user.id
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
    else:
        # Create anonymous user
        user = User(id=uuid4(), is_anonymous=True, username=f"anonymous_{uuid4().hex[:8]}")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        user_id = user.id

    # Create job
    job_id = create_job('chatgpt_import')

    # Start background import
    background_tasks.add_task(
        run_import_task,
        job_id=job_id,
        db_session=db,
        user_id=user_id,
        archive_path=archive_path,
        generate_embeddings=request.generate_embeddings
    )

    return ImportJobResponse(
        job_id=job_id,
        status='pending',
        message=f'Import job created for archive: {archive_path.name}'
    )


@router.get("/jobs/{job_id}", response_model=ImportStatusResponse)
async def get_import_status(job_id: str):
    """
    Get status of an import job.

    Args:
        job_id: Job ID from import request

    Returns:
        Current job status and progress
    """
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return ImportStatusResponse(
        job_id=job['id'],
        status=job['status'],
        progress=job.get('progress'),
        current_item=job.get('current_item'),
        total_items=job.get('total_items'),
        stats=job.get('stats'),
        error=job.get('error')
    )


@router.get("/collections", response_model=list)
async def list_imported_collections(
    user_id: Optional[str] = None,
    source_platform: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    List imported collections.

    Args:
        user_id: Filter by user ID
        source_platform: Filter by source platform (e.g., 'chatgpt')
        limit: Maximum number of results
        db: Database session

    Returns:
        List of collections
    """
    query = select(Collection).order_by(desc(Collection.created_at)).limit(limit)

    if user_id:
        try:
            user_uuid = UUID(user_id)
            query = query.where(Collection.user_id == user_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

    if source_platform:
        query = query.where(Collection.source_platform == source_platform)

    result = await db.execute(query)
    collections = result.scalars().all()

    return [col.to_dict(include_stats=True) for col in collections]


@router.post("/embeddings/process", response_model=dict)
async def process_embeddings(
    request: ProcessEmbeddingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger embedding generation for queued chunks.

    This processes chunks that were imported but don't have embeddings yet.

    Args:
        request: Processing request with max_chunks limit
        db: Database session

    Returns:
        Processing statistics
    """
    try:
        stats = await process_embeddings_now(db, max_chunks=request.max_chunks)
        return {
            'success': True,
            'stats': stats
        }
    except Exception as e:
        logger.error(f"Failed to process embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Embedding processing failed: {str(e)}")


@router.get("/embeddings/status", response_model=dict)
async def get_embeddings_status(db: AsyncSession = Depends(get_db)):
    """
    Get status of embedding generation.

    Returns count of chunks waiting for embeddings.

    Args:
        db: Database session

    Returns:
        Status information
    """
    from models.chunk_models import Chunk
    from sqlalchemy import and_, func

    # Count chunks queued for embeddings
    query = select(func.count(Chunk.id)).where(
        and_(
            Chunk.embedding.is_(None),
            Chunk.extra_metadata['embedding_queued'].as_boolean().is_(True)
        )
    )

    result = await db.execute(query)
    queued_count = result.scalar()

    # Count chunks with embeddings
    query_completed = select(func.count(Chunk.id)).where(Chunk.embedding.is_not(None))
    result_completed = await db.execute(query_completed)
    completed_count = result_completed.scalar()

    return {
        'queued': queued_count,
        'completed': completed_count,
        'total': queued_count + completed_count,
        'percent_complete': (completed_count / (queued_count + completed_count) * 100) if (queued_count + completed_count) > 0 else 100
    }


# ============================================================================
# BACKGROUND TASK RUNNER
# ============================================================================

async def run_import_task(
    job_id: str,
    db_session: AsyncSession,
    user_id: UUID,
    archive_path: Path,
    generate_embeddings: bool
):
    """
    Background task to run import.

    Args:
        job_id: Job ID
        db_session: Database session
        user_id: User ID
        archive_path: Archive path
        generate_embeddings: Whether to generate embeddings
    """
    try:
        update_job(job_id, status='running')

        # Progress callback
        def progress_callback(current: int, total: int, item_name: str):
            update_job(
                job_id,
                progress=int((current / total) * 100),
                total_items=total,
                current_item=item_name
            )

        # Run import
        stats = await import_chatgpt_archive_task(
            db_session=db_session,
            user_id=user_id,
            archive_path=archive_path,
            generate_embeddings=generate_embeddings,
            progress_callback=progress_callback
        )

        # Update job as completed
        update_job(
            job_id,
            status='completed',
            progress=100,
            stats=stats
        )

        logger.info(f"Import job {job_id} completed: {stats}")

    except Exception as e:
        logger.error(f"Import job {job_id} failed: {e}", exc_info=True)
        update_job(
            job_id,
            status='failed',
            error=str(e)
        )
