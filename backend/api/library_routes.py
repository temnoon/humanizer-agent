"""
Library API Routes

Main router that orchestrates all library browsing endpoints.

This module is a thin router orchestrator that includes sub-routers for:
- Collections (list, hierarchy, messages)
- Media (files, search, stats)
- Transformations (list, detail, reapply)

Architecture Note:
- library_routes.py: Router orchestrator (this file)
- library_schemas.py: Pydantic response models
- library_collections.py: Collection and message endpoints
- library_media.py: Media, search, and stats endpoints
- library_transformations.py: Transformation library endpoints
"""

import logging
from fastapi import APIRouter

# Import sub-routers
from .library_collections import router as collections_router
from .library_media import router as media_router
from .library_transformations import router as transformations_router

logger = logging.getLogger(__name__)

# Main router with /api/library prefix
router = APIRouter(prefix="/api/library", tags=["library"])

# Include all sub-routers
router.include_router(collections_router)
router.include_router(media_router)
router.include_router(transformations_router)
