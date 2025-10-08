"""
Pytest configuration and shared fixtures for backend tests.

Provides:
- Test database setup/teardown
- Test client for API testing
- Sample data fixtures
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import String, TypeDecorator, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from httpx import AsyncClient

# Monkey patch UUID to work with SQLite for testing
class SQLiteUUID(TypeDecorator):
    """Platform-independent UUID type that works with both PostgreSQL and SQLite."""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            from uuid import UUID as _UUID
            return _UUID(value) if isinstance(value, str) else value

from database.connection import get_db, Base
from main import app
from models.chunk_models import Collection, Message, Chunk, Media
from models.pipeline_models import TransformationJob

# Test database URL (Docker container on port 5433 for complete isolation)
TEST_DATABASE_URL = "postgresql+asyncpg://humanizer:humanizer@localhost:5433/humanizer_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with automatic cleanup.

    Each test gets a fresh database state by truncating all tables
    after the test completes.
    """
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

        # Cleanup: Truncate all tables after each test for isolation
        # TRUNCATE is faster than DROP/CREATE and resets sequences
        await session.execute(text("TRUNCATE TABLE chunk_transformations CASCADE"))
        await session.execute(text("TRUNCATE TABLE transformation_lineage CASCADE"))
        await session.execute(text("TRUNCATE TABLE transformation_jobs CASCADE"))
        await session.execute(text("TRUNCATE TABLE chunks CASCADE"))
        await session.execute(text("TRUNCATE TABLE media CASCADE"))
        await session.execute(text("TRUNCATE TABLE messages CASCADE"))
        await session.execute(text("TRUNCATE TABLE collections CASCADE"))
        await session.execute(text("TRUNCATE TABLE users CASCADE"))
        await session.execute(text("TRUNCATE TABLE book_content_links CASCADE"))
        await session.execute(text("TRUNCATE TABLE book_sections CASCADE"))
        await session.execute(text("TRUNCATE TABLE books CASCADE"))
        await session.commit()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample user for testing."""
    from uuid import uuid4
    from datetime import datetime, timezone
    from models.db_models import User

    user = User(
        id=uuid4(),
        username="test_user",
        email="test@example.com",
        preferences={},
        created_at=datetime.now(timezone.utc)
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def sample_collection(db_session: AsyncSession, sample_user) -> Collection:
    """Create a sample collection for testing."""
    from uuid import uuid4
    from datetime import datetime, timezone

    collection = Collection(
        id=uuid4(),
        user_id=sample_user.id,
        title="Test Collection",
        description="A test collection for unit testing",
        collection_type="conversation",
        source_platform="test",
        message_count=0,
        chunk_count=0,
        media_count=0,
        total_tokens=0,
        created_at=datetime.now(timezone.utc),
        import_date=datetime.now(timezone.utc),
        extra_metadata={"test": True}
    )

    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    return collection


@pytest.fixture
async def sample_message(db_session: AsyncSession, sample_collection: Collection, sample_user) -> Message:
    """Create a sample message for testing."""
    from uuid import uuid4
    from datetime import datetime, timezone

    message = Message(
        id=uuid4(),
        collection_id=sample_collection.id,
        user_id=sample_user.id,
        sequence_number=0,
        role="user",
        message_type="text",
        chunk_count=1,
        token_count=10,
        media_count=0,
        timestamp=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        extra_metadata={"test": True}
    )

    db_session.add(message)

    # Update collection message count
    sample_collection.message_count += 1

    await db_session.commit()
    await db_session.refresh(message)

    return message


@pytest.fixture
async def sample_chunk(db_session: AsyncSession, sample_message: Message, sample_user) -> Chunk:
    """Create a sample chunk for testing."""
    from uuid import uuid4
    from datetime import datetime, timezone

    chunk = Chunk(
        id=uuid4(),
        message_id=sample_message.id,
        collection_id=sample_message.collection_id,
        user_id=sample_user.id,
        content="This is a test chunk with sample content for unit testing.",
        chunk_level="message",
        chunk_sequence=0,
        token_count=10,
        is_summary=False,
        created_at=datetime.now(timezone.utc)
    )

    db_session.add(chunk)

    # Update collection chunk count
    collection = await db_session.get(Collection, sample_message.collection_id)
    collection.chunk_count += 1

    await db_session.commit()
    await db_session.refresh(chunk)

    return chunk


@pytest.fixture
async def sample_media(db_session: AsyncSession, sample_collection: Collection, sample_user) -> Media:
    """Create a sample media record for testing."""
    from uuid import uuid4
    from datetime import datetime, timezone

    media = Media(
        id=uuid4(),
        collection_id=sample_collection.id,
        user_id=sample_user.id,
        message_id=None,
        filename="test-image.jpg",
        original_media_id="test-001",
        media_type="image",
        mime_type="image/jpeg",
        file_path=None,
        width=1024,
        height=768,
        file_size=102400,
        created_at=datetime.now(timezone.utc),
        custom_metadata={"test": True}
    )

    db_session.add(media)

    # Update collection media count
    sample_collection.media_count += 1

    await db_session.commit()
    await db_session.refresh(media)

    return media


@pytest.fixture
async def sample_transformation_job(db_session: AsyncSession) -> TransformationJob:
    """Create a sample transformation job for testing."""
    from uuid import uuid4
    from datetime import datetime, timezone

    job = TransformationJob(
        id=uuid4(),
        name="Test Transformation",
        description="A test transformation job",
        job_type="persona_transform",
        status="pending",
        created_at=datetime.now(timezone.utc),
        total_items=1,
        processed_items=0,
        progress_percentage=0.0,
        tokens_used=0,
        configuration={
            "persona": "poet",
            "namespace": "romantic-literature",
            "depth": 0.5
        }
    )

    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    return job
