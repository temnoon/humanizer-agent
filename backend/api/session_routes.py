"""API routes for session and user management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db, embedding_service
from models.db_models import User, Session as DBSession, Transformation, BeliefPattern
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# Pydantic schemas for request/response
class UserCreate(BaseModel):
    """Create user request."""
    email: Optional[str] = None
    username: Optional[str] = None
    is_anonymous: bool = True


class UserResponse(BaseModel):
    """User response."""
    id: str
    email: Optional[str]
    username: Optional[str]
    is_anonymous: bool
    created_at: str
    preferences: dict


class SessionCreate(BaseModel):
    """Create session request."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    user_id: Optional[str] = None


class SessionUpdate(BaseModel):
    """Update session request."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    is_archived: Optional[bool] = None


class SessionResponse(BaseModel):
    """Session response."""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    created_at: str
    updated_at: str
    transformation_count: int
    is_archived: bool
    metadata: dict


class SessionDetailResponse(SessionResponse):
    """Detailed session response with transformations."""
    transformations: List[dict]


class TransformationCreate(BaseModel):
    """Create transformation request."""
    session_id: str
    source_text: str
    persona: str
    namespace: str
    style: str


# User endpoints
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (or anonymous user)."""
    user = User(
        email=user_data.email,
        username=user_data.username,
        is_anonymous=user_data.is_anonymous
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(**user.to_dict())


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**user.to_dict())


# Session endpoints
@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new session.

    If user_id is not provided, creates an anonymous user.
    """
    # Get or create user
    if session_data.user_id:
        try:
            user_uuid = uuid.UUID(session_data.user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        result = await db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        # Create anonymous user
        user = User(is_anonymous=True)
        db.add(user)
        await db.flush()

    # Create session
    session = DBSession(
        user_id=user.id,
        title=session_data.title,
        description=session_data.description
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(**session.to_dict())


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    user_id: Optional[str] = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List sessions.

    Can filter by user_id and archived status.
    """
    query = select(DBSession).order_by(DBSession.updated_at.desc())

    # Filter by user_id if provided
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            query = query.where(DBSession.user_id == user_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Filter archived
    if not include_archived:
        query = query.where(DBSession.is_archived == False)

    # Pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [SessionResponse(**s.to_dict()) for s in sessions]


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get session by ID with all transformations."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(
        select(DBSession)
        .where(DBSession.id == session_uuid)
        .options(selectinload(DBSession.transformations))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDetailResponse(**session.to_dict(include_transformations=True))


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update session details."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(
        select(DBSession).where(DBSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update fields
    if session_data.title is not None:
        session.title = session_data.title
    if session_data.description is not None:
        session.description = session_data.description
    if session_data.is_archived is not None:
        session.is_archived = session_data.is_archived

    await db.commit()
    await db.refresh(session)

    return SessionResponse(**session.to_dict())


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a session and all its transformations."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(
        delete(DBSession).where(DBSession.id == session_uuid)
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.commit()


@router.post("/{session_id}/clone", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def clone_session(
    session_id: str,
    new_title: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Clone a session (creates new session with same title + " (Copy)").

    Does not copy transformations, only session metadata.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(
        select(DBSession).where(DBSession.id == session_uuid)
    )
    original_session = result.scalar_one_or_none()

    if not original_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create cloned session
    cloned_session = DBSession(
        user_id=original_session.user_id,
        title=new_title or f"{original_session.title} (Copy)",
        description=original_session.description,
        metadata=original_session.metadata
    )
    db.add(cloned_session)
    await db.commit()
    await db.refresh(cloned_session)

    return SessionResponse(**cloned_session.to_dict())


@router.get("/{session_id}/similar", response_model=List[dict])
async def find_similar_sessions(
    session_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Find sessions with similar content using vector search.

    Compares average embeddings of transformations within sessions.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # TODO: Implement vector similarity search
    # This requires aggregating embeddings from transformations
    # and using pgvector's cosine similarity operators

    return []


# Transformation query endpoints
@router.get("/{session_id}/transformations", response_model=List[dict])
async def list_session_transformations(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all transformations in a session."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(
        select(Transformation)
        .where(Transformation.session_id == session_uuid)
        .order_by(Transformation.created_at)
    )
    transformations = result.scalars().all()

    return [t.to_dict() for t in transformations]


@router.get("/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get session statistics.

    Returns: total transformations, unique personas/namespaces/styles,
    total tokens used, date range.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Check session exists
    result = await db.execute(
        select(DBSession).where(DBSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get transformation stats
    result = await db.execute(
        select(
            func.count(Transformation.id).label("total_count"),
            func.sum(Transformation.tokens_used).label("total_tokens"),
            func.min(Transformation.created_at).label("first_transformation"),
            func.max(Transformation.created_at).label("last_transformation"),
        )
        .where(Transformation.session_id == session_uuid)
    )
    stats = result.one()

    # Get unique frameworks
    result = await db.execute(
        select(
            func.array_agg(func.distinct(Transformation.persona)).label("personas"),
            func.array_agg(func.distinct(Transformation.namespace)).label("namespaces"),
            func.array_agg(func.distinct(Transformation.style)).label("styles"),
        )
        .where(Transformation.session_id == session_uuid)
    )
    frameworks = result.one()

    return {
        "session_id": session_id,
        "title": session.title,
        "total_transformations": stats.total_count or 0,
        "total_tokens_used": stats.total_tokens or 0,
        "first_transformation": stats.first_transformation.isoformat() if stats.first_transformation else None,
        "last_transformation": stats.last_transformation.isoformat() if stats.last_transformation else None,
        "unique_personas": frameworks.personas or [],
        "unique_namespaces": frameworks.namespaces or [],
        "unique_styles": frameworks.styles or [],
    }
