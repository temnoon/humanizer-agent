"""
Tests for Library API - Collection Endpoints

Tests:
- GET /api/library/collections
- GET /api/library/collections/{collection_id}
- GET /api/library/stats
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from models.chunk_models import Collection, Message, Chunk


class TestListCollections:
    """Tests for GET /api/library/collections"""

    async def test_list_collections_empty(self, client: AsyncClient):
        """Test listing collections when database is empty."""
        response = await client.get("/api/library/collections")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_collections_with_data(
        self, client: AsyncClient, sample_collection: Collection
    ):
        """Test listing collections with one collection in database."""
        response = await client.get("/api/library/collections")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(sample_collection.id)
        assert data[0]["title"] == "Test Collection"
        assert data[0]["collection_type"] == "conversation"
        assert data[0]["source_platform"] == "test"

    async def test_list_collections_filter_by_platform(
        self, client: AsyncClient, db_session: AsyncSession, sample_user
    ):
        """Test filtering collections by source platform."""
        from datetime import datetime, timezone

        # Create collections with different platforms
        col1 = Collection(
            id=uuid4(),
            user_id=sample_user.id,
            title="ChatGPT Collection",
            collection_type="conversation",
            source_platform="chatgpt",
            message_count=0,
            chunk_count=0,
            media_count=0,
            total_tokens=0,
            created_at=datetime.now(timezone.utc)
        )
        col2 = Collection(
            id=uuid4(),
            user_id=sample_user.id,
            title="Claude Collection",
            collection_type="conversation",
            source_platform="claude",
            message_count=0,
            chunk_count=0,
            media_count=0,
            total_tokens=0,
            created_at=datetime.now(timezone.utc)
        )

        db_session.add_all([col1, col2])
        await db_session.commit()

        # Filter by chatgpt
        response = await client.get("/api/library/collections?source_platform=chatgpt")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source_platform"] == "chatgpt"

        # Filter by claude
        response = await client.get("/api/library/collections?source_platform=claude")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source_platform"] == "claude"

    async def test_list_collections_search(
        self, client: AsyncClient, db_session: AsyncSession, sample_user
    ):
        """Test search functionality in collections."""
        from datetime import datetime, timezone

        # Create collections with different titles
        col1 = Collection(
            id=uuid4(),
            user_id=sample_user.id,
            title="Machine Learning Basics",
            collection_type="conversation",
            source_platform="test",
            message_count=0,
            chunk_count=0,
            media_count=0,
            total_tokens=0,
            created_at=datetime.now(timezone.utc)
        )
        col2 = Collection(
            id=uuid4(),
            user_id=sample_user.id,
            title="Python Programming",
            collection_type="conversation",
            source_platform="test",
            message_count=0,
            chunk_count=0,
            media_count=0,
            total_tokens=0,
            created_at=datetime.now(timezone.utc)
        )

        db_session.add_all([col1, col2])
        await db_session.commit()

        # Search for "learning"
        response = await client.get("/api/library/collections?search=learning")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Learning" in data[0]["title"]

        # Search for "python"
        response = await client.get("/api/library/collections?search=python")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Python" in data[0]["title"]

    async def test_list_collections_pagination(
        self, client: AsyncClient, db_session: AsyncSession, sample_user
    ):
        """Test pagination with limit and offset."""
        from datetime import datetime, timezone

        # Create 5 collections
        collections = []
        for i in range(5):
            col = Collection(
                id=uuid4(),
                user_id=sample_user.id,
                title=f"Collection {i}",
                collection_type="conversation",
                source_platform="test",
                message_count=0,
                chunk_count=0,
                media_count=0,
                total_tokens=0,
                created_at=datetime.now(timezone.utc)
            )
            collections.append(col)

        db_session.add_all(collections)
        await db_session.commit()

        # Get first 2
        response = await client.get("/api/library/collections?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get next 2
        response = await client.get("/api/library/collections?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get last 1
        response = await client.get("/api/library/collections?limit=2&offset=4")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestGetCollectionHierarchy:
    """Tests for GET /api/library/collections/{collection_id}"""

    async def test_get_collection_hierarchy_basic(
        self, client: AsyncClient, sample_collection: Collection
    ):
        """Test getting collection hierarchy."""
        response = await client.get(f"/api/library/collections/{sample_collection.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["collection"]["id"] == str(sample_collection.id)
        assert data["collection"]["title"] == "Test Collection"
        assert "messages" in data
        assert isinstance(data["messages"], list)

    async def test_get_collection_hierarchy_with_messages(
        self, client: AsyncClient, sample_collection: Collection, sample_message: Message
    ):
        """Test getting collection hierarchy with messages."""
        response = await client.get(f"/api/library/collections/{sample_collection.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 1
        assert data["messages"][0]["id"] == str(sample_message.id)
        assert data["messages"][0]["role"] == "user"

    async def test_get_collection_hierarchy_with_chunks(
        self, client: AsyncClient, sample_collection: Collection,
        sample_message: Message, sample_chunk: Chunk
    ):
        """Test getting collection hierarchy with chunks included."""
        response = await client.get(
            f"/api/library/collections/{sample_collection.id}?include_chunks=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert "recent_chunks" in data
        assert len(data["recent_chunks"]) == 1
        assert data["recent_chunks"][0]["content"] == sample_chunk.content

    async def test_get_collection_hierarchy_not_found(self, client: AsyncClient):
        """Test 404 error when collection doesn't exist."""
        fake_id = uuid4()
        response = await client.get(f"/api/library/collections/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_collection_hierarchy_invalid_uuid(self, client: AsyncClient):
        """Test 400 error with invalid UUID format."""
        response = await client.get("/api/library/collections/invalid-uuid")

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestLibraryStats:
    """Tests for GET /api/library/stats"""

    async def test_stats_empty_database(self, client: AsyncClient):
        """Test stats endpoint with empty database."""
        response = await client.get("/api/library/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["collections"] == 0
        assert data["messages"] == 0
        assert data["chunks"] == 0
        assert data["media_files"] == 0

    async def test_stats_with_data(
        self, client: AsyncClient, sample_collection: Collection,
        sample_message: Message, sample_chunk: Chunk
    ):
        """Test stats endpoint with data."""
        response = await client.get("/api/library/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["collections"] == 1
        assert data["messages"] == 1
        assert data["chunks"] == 1
        assert "platforms" in data
