"""
Book Builder API Routes

Endpoints for creating and managing books/papers with hierarchical sections.
Inspired by Joplin's notebook structure but focused on academic/technical writing.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from sqlalchemy.orm import selectinload

from database.connection import get_db
from models.book_models import Book, BookSection, BookContentLink
from models.chunk_models import Chunk
from models.pipeline_models import TransformationJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/books", tags=["books"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class BookCreate(BaseModel):
    """Request model for creating a book."""
    title: str
    subtitle: Optional[str] = None
    book_type: str = 'paper'
    configuration: dict = {}
    custom_metadata: dict = {}


class BookUpdate(BaseModel):
    """Request model for updating a book."""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    book_type: Optional[str] = None
    configuration: Optional[dict] = None
    custom_metadata: Optional[dict] = None


class SectionCreate(BaseModel):
    """Request model for creating a section."""
    title: str
    parent_section_id: Optional[str] = None
    section_type: Optional[str] = None
    sequence_number: int
    content: Optional[str] = None
    custom_metadata: dict = {}


class SectionUpdate(BaseModel):
    """Request model for updating a section."""
    title: Optional[str] = None
    sequence_number: Optional[int] = None
    content: Optional[str] = None
    custom_metadata: Optional[dict] = None


class ContentLinkCreate(BaseModel):
    """Request model for adding content to a section."""
    chunk_id: Optional[str] = None
    transformation_job_id: Optional[str] = None
    sequence_number: Optional[int] = None
    notes: Optional[str] = None


# ============================================================================
# BOOK ENDPOINTS
# ============================================================================

@router.post("/", status_code=201)
async def create_book(
    book: BookCreate,
    user_id: str = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new book."""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    new_book = Book(
        user_id=user_uuid,
        title=book.title,
        subtitle=book.subtitle,
        book_type=book.book_type,
        configuration=book.configuration,
        custom_metadata=book.custom_metadata
    )

    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)

    return new_book.to_dict()


@router.get("/")
async def list_books(
    user_id: Optional[str] = Query(None, description="User ID (optional - shows all books if not provided)"),
    book_type: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all books, optionally filtered by user_id."""
    query = select(Book).order_by(desc(Book.updated_at))

    # Optional user filtering
    if user_id:
        try:
            user_uuid = UUID(user_id)
            query = query.where(Book.user_id == user_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

    if book_type:
        query = query.where(Book.book_type == book_type)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    books = result.scalars().all()

    return [book.to_dict() for book in books]


@router.get("/{book_id}")
async def get_book(
    book_id: str,
    include_sections: bool = Query(False, description="Include sections in response"),
    db: AsyncSession = Depends(get_db)
):
    """Get a book by ID."""
    try:
        book_uuid = UUID(book_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid book ID format")

    if include_sections:
        result = await db.execute(
            select(Book)
            .options(selectinload(Book.sections))
            .where(Book.id == book_uuid)
        )
    else:
        result = await db.execute(select(Book).where(Book.id == book_uuid))

    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return book.to_dict(include_sections=include_sections)


@router.patch("/{book_id}")
async def update_book(
    book_id: str,
    book_update: BookUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a book."""
    try:
        book_uuid = UUID(book_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid book ID format")

    result = await db.execute(select(Book).where(Book.id == book_uuid))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Update fields
    if book_update.title is not None:
        book.title = book_update.title
    if book_update.subtitle is not None:
        book.subtitle = book_update.subtitle
    if book_update.book_type is not None:
        book.book_type = book_update.book_type
    if book_update.configuration is not None:
        book.configuration = book_update.configuration
    if book_update.custom_metadata is not None:
        book.custom_metadata = book_update.custom_metadata

    await db.commit()
    await db.refresh(book)

    return book.to_dict()


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a book."""
    try:
        book_uuid = UUID(book_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid book ID format")

    result = await db.execute(select(Book).where(Book.id == book_uuid))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    await db.delete(book)
    await db.commit()


# ============================================================================
# SECTION ENDPOINTS
# ============================================================================

@router.post("/{book_id}/sections", status_code=201)
async def create_section(
    book_id: str,
    section: SectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new section in a book."""
    try:
        book_uuid = UUID(book_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid book ID format")

    # Verify book exists
    result = await db.execute(select(Book).where(Book.id == book_uuid))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Verify parent section exists if specified
    parent_uuid = None
    if section.parent_section_id:
        try:
            parent_uuid = UUID(section.parent_section_id)
            parent_result = await db.execute(select(BookSection).where(BookSection.id == parent_uuid))
            if not parent_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Parent section not found")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent section ID format")

    new_section = BookSection(
        book_id=book_uuid,
        parent_section_id=parent_uuid,
        title=section.title,
        section_type=section.section_type,
        sequence_number=section.sequence_number,
        content=section.content,
        custom_metadata=section.custom_metadata
    )

    db.add(new_section)
    await db.commit()
    await db.refresh(new_section)

    return new_section.to_dict()


@router.get("/{book_id}/sections")
async def list_sections(
    book_id: str,
    parent_id: Optional[str] = Query(None, description="Filter by parent section ID"),
    db: AsyncSession = Depends(get_db)
):
    """List all sections in a book."""
    try:
        book_uuid = UUID(book_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid book ID format")

    query = select(BookSection).where(BookSection.book_id == book_uuid)

    if parent_id:
        try:
            parent_uuid = UUID(parent_id)
            query = query.where(BookSection.parent_section_id == parent_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent ID format")
    else:
        # Top-level sections only
        query = query.where(BookSection.parent_section_id.is_(None))

    query = query.order_by(BookSection.sequence_number)

    result = await db.execute(query)
    sections = result.scalars().all()

    return [section.to_dict() for section in sections]


@router.get("/{book_id}/sections/{section_id}")
async def get_section(
    book_id: str,
    section_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a section by ID."""
    try:
        section_uuid = UUID(section_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid section ID format")

    result = await db.execute(select(BookSection).where(BookSection.id == section_uuid))
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    return section.to_dict()


@router.patch("/{book_id}/sections/{section_id}")
async def update_section(
    book_id: str,
    section_id: str,
    section_update: SectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a section."""
    try:
        section_uuid = UUID(section_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid section ID format")

    result = await db.execute(select(BookSection).where(BookSection.id == section_uuid))
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Update fields
    if section_update.title is not None:
        section.title = section_update.title
    if section_update.sequence_number is not None:
        section.sequence_number = section_update.sequence_number
    if section_update.content is not None:
        section.content = section_update.content
    if section_update.custom_metadata is not None:
        section.custom_metadata = section_update.custom_metadata

    await db.commit()
    await db.refresh(section)

    return section.to_dict()


@router.delete("/{book_id}/sections/{section_id}", status_code=204)
async def delete_section(
    book_id: str,
    section_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a section."""
    try:
        section_uuid = UUID(section_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid section ID format")

    result = await db.execute(select(BookSection).where(BookSection.id == section_uuid))
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    await db.delete(section)
    await db.commit()


# ============================================================================
# CONTENT LINK ENDPOINTS
# ============================================================================

@router.post("/{book_id}/sections/{section_id}/content", status_code=201)
async def add_content_to_section(
    book_id: str,
    section_id: str,
    content_link: ContentLinkCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add content (chunk or transformation result) to a section."""
    try:
        section_uuid = UUID(section_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid section ID format")

    # Verify section exists
    result = await db.execute(select(BookSection).where(BookSection.id == section_uuid))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Parse UUIDs
    chunk_uuid = None
    if content_link.chunk_id:
        try:
            chunk_uuid = UUID(content_link.chunk_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid chunk ID format")

    job_uuid = None
    if content_link.transformation_job_id:
        try:
            job_uuid = UUID(content_link.transformation_job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid transformation job ID format")

    # At least one content source must be specified
    if not chunk_uuid and not job_uuid:
        raise HTTPException(status_code=400, detail="Must specify chunk_id or transformation_job_id")

    new_link = BookContentLink(
        section_id=section_uuid,
        chunk_id=chunk_uuid,
        transformation_job_id=job_uuid,
        sequence_number=content_link.sequence_number,
        notes=content_link.notes
    )

    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)

    return new_link.to_dict()


@router.get("/{book_id}/sections/{section_id}/content")
async def list_section_content(
    book_id: str,
    section_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List all content links in a section with full content from chunks/jobs."""
    try:
        section_uuid = UUID(section_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid section ID format")

    result = await db.execute(
        select(BookContentLink)
        .options(
            selectinload(BookContentLink.chunk),
            selectinload(BookContentLink.transformation_job)
        )
        .where(BookContentLink.section_id == section_uuid)
        .order_by(BookContentLink.sequence_number)
    )
    links = result.scalars().all()

    # Enrich links with actual content
    enriched_links = []
    for link in links:
        link_data = link.to_dict()

        # Add chunk content if present
        if link.chunk:
            link_data['chunk_content'] = link.chunk.content
            link_data['chunk_metadata'] = {
                'message_id': str(link.chunk.message_id) if link.chunk.message_id else None,
                'collection_id': str(link.chunk.collection_id) if link.chunk.collection_id else None,
            }

        # Add transformation job result if present
        if link.transformation_job:
            link_data['job_content'] = link.transformation_job.result
            link_data['job_metadata'] = {
                'job_type': link.transformation_job.job_type,
                'status': link.transformation_job.status,
                'source_message_id': str(link.transformation_job.source_message_id) if link.transformation_job.source_message_id else None,
            }

        enriched_links.append(link_data)

    return enriched_links


@router.delete("/{book_id}/sections/{section_id}/content/{link_id}", status_code=204)
async def remove_content_from_section(
    book_id: str,
    section_id: str,
    link_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a content link from a section."""
    try:
        link_uuid = UUID(link_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid link ID format")

    result = await db.execute(select(BookContentLink).where(BookContentLink.id == link_uuid))
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=404, detail="Content link not found")

    await db.delete(link)
    await db.commit()
