"""
Gizmo Mapping API Routes

Endpoints for managing Custom GPT (gizmo_id) to human-readable name mappings.
"""

import logging
from typing import Optional, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert

from database.connection import get_db
from models.chunk_models import Collection, Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gizmos", tags=["gizmos"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class GizmoMapping(BaseModel):
    """Gizmo ID to custom name mapping."""
    gizmo_id: str
    custom_name: str
    user_id: str
    metadata: Optional[Dict] = {}


class GizmoMappingRequest(BaseModel):
    """Request to create/update gizmo mapping."""
    gizmo_id: str
    custom_name: str


class GizmoInfo(BaseModel):
    """Extended gizmo information with usage stats."""
    gizmo_id: str
    custom_name: Optional[str]
    message_count: int
    collection_count: int
    first_seen: Optional[str]
    last_seen: Optional[str]


# ============================================================================
# GIZMO MAPPING ENDPOINTS
# ============================================================================

@router.get("/mappings", response_model=Dict[str, str])
async def get_user_gizmo_mappings(
    user_id: str = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all gizmo mappings for a user.

    Returns a dictionary of gizmo_id -> custom_name.

    For now, we'll store mappings in user preferences in the users table.
    """
    from models.db_models import User

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Get user preferences
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Extract gizmo mappings from preferences
    preferences = user.preferences or {}
    gizmo_mappings = preferences.get('gizmo_mappings', {})

    return gizmo_mappings


@router.put("/mappings", response_model=Dict[str, str])
async def update_gizmo_mapping(
    request: GizmoMappingRequest,
    user_id: str = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update a gizmo mapping for a user.

    This will store the mapping in user preferences and return
    all mappings for the user.
    """
    from models.db_models import User

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Get user
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update preferences with new mapping
    preferences = user.preferences or {}
    gizmo_mappings = preferences.get('gizmo_mappings', {})
    gizmo_mappings[request.gizmo_id] = request.custom_name
    preferences['gizmo_mappings'] = gizmo_mappings

    # Update user
    await db.execute(
        update(User)
        .where(User.id == user_uuid)
        .values(preferences=preferences)
    )
    await db.commit()

    logger.info(f"Updated gizmo mapping: {request.gizmo_id} -> {request.custom_name}")

    return gizmo_mappings


@router.delete("/mappings/{gizmo_id}", response_model=Dict[str, str])
async def delete_gizmo_mapping(
    gizmo_id: str,
    user_id: str = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a gizmo mapping for a user.

    Returns remaining mappings.
    """
    from models.db_models import User

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Get user
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Remove mapping from preferences
    preferences = user.preferences or {}
    gizmo_mappings = preferences.get('gizmo_mappings', {})

    if gizmo_id in gizmo_mappings:
        del gizmo_mappings[gizmo_id]
        preferences['gizmo_mappings'] = gizmo_mappings

        # Update user
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(preferences=preferences)
        )
        await db.commit()

        logger.info(f"Deleted gizmo mapping: {gizmo_id}")

    return gizmo_mappings


@router.get("/info", response_model=List[GizmoInfo])
async def get_gizmo_info(
    user_id: str = Query(..., description="User ID"),
    collection_id: Optional[str] = Query(None, description="Filter by collection"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about gizmos used in a user's collections.

    Includes custom names (if set) and usage statistics.
    """
    from models.db_models import User
    from sqlalchemy import func, distinct

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Get user's gizmo mappings
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    gizmo_mappings = (user.preferences or {}).get('gizmo_mappings', {})

    # Build query for gizmo usage
    # Gizmo IDs are in message metadata
    # Build WHERE conditions first to avoid GROUP BY issues
    where_conditions = [
        Message.user_id == user_uuid,
        Message.extra_metadata['gizmo_id'].astext.is_not(None)
    ]

    if collection_id:
        try:
            col_uuid = UUID(collection_id)
            where_conditions.append(Message.collection_id == col_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid collection ID format")

    gizmo_id_expr = Message.extra_metadata['gizmo_id'].astext
    query = select(
        gizmo_id_expr.label('gizmo_id'),
        func.count(Message.id).label('message_count'),
        func.count(distinct(Message.collection_id)).label('collection_count'),
        func.min(Message.created_at).label('first_seen'),
        func.max(Message.created_at).label('last_seen')
    ).where(
        *where_conditions
    ).group_by(
        gizmo_id_expr
    )

    results = await db.execute(query)
    gizmo_stats = results.all()

    # Build response
    gizmo_info_list = []
    for stat in gizmo_stats:
        if stat.gizmo_id and stat.gizmo_id != 'null':
            gizmo_info_list.append(GizmoInfo(
                gizmo_id=stat.gizmo_id,
                custom_name=gizmo_mappings.get(stat.gizmo_id),
                message_count=stat.message_count,
                collection_count=stat.collection_count,
                first_seen=stat.first_seen.isoformat() if stat.first_seen else None,
                last_seen=stat.last_seen.isoformat() if stat.last_seen else None
            ))

    return gizmo_info_list


@router.get("/collection/{collection_id}", response_model=List[str])
async def get_collection_gizmos(
    collection_id: str,
    include_names: bool = Query(False, description="Include custom names instead of IDs"),
    user_id: Optional[str] = Query(None, description="User ID for custom name lookup"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all unique gizmo IDs used in a collection.

    Optionally resolve to custom names if user_id is provided.
    """
    from models.db_models import User
    from sqlalchemy import func, distinct

    try:
        col_uuid = UUID(collection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection ID format")

    # Get unique gizmo IDs from messages in collection
    query = select(
        distinct(Message.extra_metadata['gizmo_id'].astext)
    ).where(
        Message.collection_id == col_uuid,
        Message.extra_metadata['gizmo_id'].astext.is_not(None)
    )

    results = await db.execute(query)
    gizmo_ids = [row[0] for row in results.all() if row[0] and row[0] != 'null']

    # If include_names requested and user_id provided, resolve names
    if include_names and user_id:
        try:
            user_uuid = UUID(user_id)

            # Get user's gizmo mappings
            user_result = await db.execute(
                select(User).where(User.id == user_uuid)
            )
            user = user_result.scalar_one_or_none()

            if user:
                gizmo_mappings = (user.preferences or {}).get('gizmo_mappings', {})
                return [gizmo_mappings.get(gid, gid) for gid in gizmo_ids]
        except ValueError:
            pass  # Invalid user_id, just return IDs

    return gizmo_ids
