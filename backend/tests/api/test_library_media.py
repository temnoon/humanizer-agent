"""
Tests for Library API - Media Endpoints

Tests:
- GET /api/library/media
- GET /api/library/media/{media_id}/metadata
- GET /api/library/media/{media_id}/file
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from models.chunk_models import Media, Collection


class TestListMedia:
    """Tests for GET /api/library/media"""

    async def test_list_media_empty(self, client: AsyncClient):
        """Test listing media when database is empty."""
        response = await client.get("/api/library/media")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_media_with_data(
        self, client: AsyncClient, sample_media: Media
    ):
        """Test listing media with one media record."""
        response = await client.get("/api/library/media")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(sample_media.id)
        assert data[0]["filename"] == "test-image.jpg"
        assert data[0]["media_type"] == "image"

    async def test_list_media_filter_by_type(
        self, client: AsyncClient, db_session: AsyncSession, sample_collection: Collection
    ):
        """Test filtering media by type."""
        from datetime import datetime, timezone

        # Create media of different types
        image = Media(
            id=uuid4(),
            collection_id=sample_collection.id,
            filename="image.jpg",
            original_media_id="img-001",
            media_type="image",
            mime_type="image/jpeg",
            created_at=datetime.now(timezone.utc),
            custom_metadata={}
        )
        video = Media(
            id=uuid4(),
            collection_id=sample_collection.id,
            filename="video.mp4",
            original_media_id="vid-001",
            media_type="video",
            mime_type="video/mp4",
            created_at=datetime.now(timezone.utc),
            custom_metadata={}
        )

        db_session.add_all([image, video])
        await db_session.commit()

        # Filter by image
        response = await client.get("/api/library/media?media_type=image")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["media_type"] == "image"

    async def test_list_media_search(
        self, client: AsyncClient, db_session: AsyncSession, sample_collection: Collection
    ):
        """Test search functionality in media."""
        from datetime import datetime, timezone

        # Create media with different filenames
        media1 = Media(
            id=uuid4(),
            collection_id=sample_collection.id,
            filename="vacation-beach.jpg",
            original_media_id="media-001",
            media_type="image",
            mime_type="image/jpeg",
            created_at=datetime.now(timezone.utc),
            custom_metadata={}
        )
        media2 = Media(
            id=uuid4(),
            collection_id=sample_collection.id,
            filename="work-presentation.pdf",
            original_media_id="media-002",
            media_type="document",
            mime_type="application/pdf",
            created_at=datetime.now(timezone.utc),
            custom_metadata={}
        )

        db_session.add_all([media1, media2])
        await db_session.commit()

        # Search for "beach"
        response = await client.get("/api/library/media?search=beach")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "beach" in data[0]["filename"]

    async def test_list_media_pagination(
        self, client: AsyncClient, db_session: AsyncSession, sample_collection: Collection
    ):
        """Test pagination with limit and offset."""
        from datetime import datetime, timezone

        # Create 5 media files
        media_files = []
        for i in range(5):
            media = Media(
                id=uuid4(),
                collection_id=sample_collection.id,
                filename=f"file-{i}.jpg",
                original_media_id=f"media-{i}",
                media_type="image",
                mime_type="image/jpeg",
                created_at=datetime.now(timezone.utc),
                custom_metadata={}
            )
            media_files.append(media)

        db_session.add_all(media_files)
        await db_session.commit()

        # Get first 2
        response = await client.get("/api/library/media?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestGetMediaMetadata:
    """Tests for GET /api/library/media/{media_id}/metadata"""

    async def test_get_media_metadata(
        self, client: AsyncClient, sample_media: Media
    ):
        """Test getting media metadata."""
        response = await client.get(f"/api/library/media/{sample_media.id}/metadata")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_media.id)
        assert data["filename"] == "test-image.jpg"
        assert data["media_type"] == "image"
        assert data["width"] == 1024
        assert data["height"] == 768

    async def test_get_media_metadata_not_found(self, client: AsyncClient):
        """Test 404 error when media doesn't exist."""
        fake_id = uuid4()
        response = await client.get(f"/api/library/media/{fake_id}/metadata")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_media_metadata_invalid_uuid(self, client: AsyncClient):
        """Test 400 error with invalid UUID format."""
        response = await client.get("/api/library/media/invalid-uuid/metadata")

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestGetMediaFile:
    """Tests for GET /api/library/media/{media_id}/file"""

    async def test_get_media_file_no_path(
        self, client: AsyncClient, sample_media: Media
    ):
        """Test 404 when media has no file_path."""
        response = await client.get(f"/api/library/media/{sample_media.id}/file")

        assert response.status_code == 404
        assert "file not found" in response.json()["detail"].lower()

    async def test_get_media_file_not_found(self, client: AsyncClient):
        """Test 404 error when media doesn't exist."""
        fake_id = uuid4()
        response = await client.get(f"/api/library/media/{fake_id}/file")

        assert response.status_code == 404

    async def test_get_media_file_invalid_uuid(self, client: AsyncClient):
        """Test 400 error with invalid UUID format."""
        response = await client.get("/api/library/media/invalid-uuid/file")

        assert response.status_code == 400
