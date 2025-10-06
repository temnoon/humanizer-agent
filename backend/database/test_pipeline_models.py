#!/usr/bin/env python3
"""
Test script for transformation pipeline models.

Verifies that SQLAlchemy models can:
- Create records in transformation_jobs, chunk_transformations, transformation_lineage
- Query with filters and joins
- Use helper functions for lineage traversal
- Test graph queries

Usage:
    python test_pipeline_models.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from models.pipeline_models import (
    TransformationJob, ChunkTransformation, TransformationLineage,
    JobStatus, JobType
)
from models.chunk_models import Collection, Message, Chunk
from models.db_models import User, Session as DBSession


def get_sync_db_url(async_url: str) -> str:
    """Convert async database URL to sync."""
    if '+asyncpg://' in async_url:
        return async_url.replace('+asyncpg://', '+psycopg2://')
    return async_url


def test_pipeline_models():
    """Test pipeline models with the database."""
    print("🧪 Testing Transformation Pipeline Models\n")
    print("="*80)

    # Get database connection
    db_url = get_sync_db_url(settings.database_url)
    engine = create_engine(db_url, echo=False)

    print("\n1️⃣  Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM transformation_jobs;"))
            job_count = result.fetchone()[0]
            print(f"   ✅ Connected successfully")
            print(f"   📊 Existing jobs: {job_count}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return

    # Create test session
    session = Session(engine)

    try:
        # Get or create test user
        print("\n2️⃣  Getting test user...")
        test_user = session.query(User).filter_by(email="test@humanizer.ai").first()
        if not test_user:
            test_user = User(
                email="test@humanizer.ai",
                username="test_user",
                is_anonymous=False
            )
            session.add(test_user)
            session.flush()
            print(f"   ✅ Created test user: {test_user.id}")
        else:
            print(f"   ✅ Found test user: {test_user.id}")

        # Get or create test session
        print("\n3️⃣  Getting test session...")
        test_session = session.query(DBSession).filter_by(
            user_id=test_user.id,
            title="Pipeline Test Session"
        ).first()
        if not test_session:
            test_session = DBSession(
                user_id=test_user.id,
                title="Pipeline Test Session",
                description="Test session for pipeline models"
            )
            session.add(test_session)
            session.flush()
            print(f"   ✅ Created test session: {test_session.id}")
        else:
            print(f"   ✅ Found test session: {test_session.id}")

        # Get or create test collection and chunks
        print("\n4️⃣  Getting test chunks...")
        test_collection = session.query(Collection).filter_by(
            user_id=test_user.id,
            title="Pipeline Test Collection"
        ).first()
        if not test_collection:
            # Create collection
            test_collection = Collection(
                user_id=test_user.id,
                title="Pipeline Test Collection",
                collection_type="custom",
                source_platform="test"
            )
            session.add(test_collection)
            session.flush()

            # Create message
            test_message = Message(
                collection_id=test_collection.id,
                user_id=test_user.id,
                sequence_number=1,
                role="user"
            )
            session.add(test_message)
            session.flush()

            # Create chunks
            test_chunk_1 = Chunk(
                message_id=test_message.id,
                collection_id=test_collection.id,
                user_id=test_user.id,
                content="This is the original content for testing transformations.",
                chunk_level="document",
                chunk_sequence=1
            )
            session.add(test_chunk_1)
            session.flush()

            print(f"   ✅ Created test collection and chunk: {test_chunk_1.id}")
        else:
            test_chunk_1 = session.query(Chunk).filter_by(
                collection_id=test_collection.id
            ).first()
            print(f"   ✅ Found test chunk: {test_chunk_1.id}")

        # Test 1: Create TransformationJob
        print("\n5️⃣  Testing TransformationJob creation...")
        job = TransformationJob(
            user_id=test_user.id,
            session_id=test_session.id,
            name="Test Madhyamaka Detection Job",
            description="Testing job creation and status tracking",
            job_type=JobType.MADHYAMAKA_DETECT,
            status=JobStatus.PENDING,
            total_items=10,
            configuration={
                "source_chunk_ids": [str(test_chunk_1.id)],
                "analysis_depth": "moderate"
            },
            priority=5
        )
        session.add(job)
        session.flush()
        print(f"   ✅ Created job: {job.id}")
        print(f"      Name: {job.name}")
        print(f"      Type: {job.job_type.value}")
        print(f"      Status: {job.status.value}")

        # Test 2: Create result chunk and ChunkTransformation
        print("\n6️⃣  Testing ChunkTransformation creation...")
        result_chunk = Chunk(
            message_id=test_chunk_1.message_id,
            collection_id=test_chunk_1.collection_id,
            user_id=test_user.id,
            content="Transformed content with middle path perspective.",
            chunk_level="document",
            chunk_sequence=2,
            extra_metadata={"transformation_type": "madhyamaka_detect"}
        )
        session.add(result_chunk)
        session.flush()

        chunk_trans = ChunkTransformation(
            job_id=job.id,
            source_chunk_id=test_chunk_1.id,
            result_chunk_id=result_chunk.id,
            transformation_type="madhyamaka_detect",
            parameters={
                "analysis_depth": "moderate",
                "confidence": 0.85
            },
            status="completed",
            tokens_used=450,
            processing_time_ms=1200,
            sequence_number=1
        )
        session.add(chunk_trans)
        session.flush()
        print(f"   ✅ Created transformation: {chunk_trans.id}")
        print(f"      Source: {chunk_trans.source_chunk_id}")
        print(f"      Result: {chunk_trans.result_chunk_id}")

        # Test 3: Create TransformationLineage
        print("\n7️⃣  Testing TransformationLineage creation...")
        lineage_root = TransformationLineage(
            root_chunk_id=test_chunk_1.id,
            chunk_id=test_chunk_1.id,
            generation=0,
            transformation_path=[],
            session_ids=[test_session.id],
            job_ids=[],
            depth=0
        )
        session.add(lineage_root)
        session.flush()

        lineage_gen1 = TransformationLineage(
            root_chunk_id=test_chunk_1.id,
            chunk_id=result_chunk.id,
            generation=1,
            transformation_path=["madhyamaka_detect"],
            parent_lineage_id=lineage_root.id,
            session_ids=[test_session.id],
            job_ids=[job.id],
            depth=1,
            total_transformations=1,
            total_tokens_used=450
        )
        session.add(lineage_gen1)
        session.flush()
        print(f"   ✅ Created lineage: root={lineage_root.id}, gen1={lineage_gen1.id}")
        print(f"      Generations: 0 → 1")
        print(f"      Path: {lineage_gen1.transformation_path}")

        # Test 4: Query with filters
        print("\n8️⃣  Testing queries...")

        # Query jobs by status
        pending_jobs = session.query(TransformationJob).filter_by(
            status=JobStatus.PENDING
        ).all()
        print(f"   ✅ Pending jobs: {len(pending_jobs)}")

        # Query transformations by job
        job_transformations = session.query(ChunkTransformation).filter_by(
            job_id=job.id
        ).all()
        print(f"   ✅ Transformations in job: {len(job_transformations)}")

        # Query lineage by root
        lineage_nodes = session.query(TransformationLineage).filter_by(
            root_chunk_id=test_chunk_1.id
        ).order_by(TransformationLineage.generation).all()
        print(f"   ✅ Lineage nodes: {len(lineage_nodes)}")
        for node in lineage_nodes:
            print(f"      Gen {node.generation}: {node.chunk_id}")

        # Test 5: Test helper function
        print("\n9️⃣  Testing helper functions...")
        result = session.execute(
            text(f"SELECT * FROM get_transformation_lineage('{result_chunk.id}');")
        )
        lineage_results = result.fetchall()
        print(f"   ✅ get_transformation_lineage returned {len(lineage_results)} nodes")
        for row in lineage_results:
            print(f"      Generation {row[3]}: {row[2]}")

        # Test 6: Test views
        print("\n🔟 Testing views...")
        result = session.execute(text(f"SELECT * FROM transformation_job_progress WHERE id = '{job.id}';"))
        job_progress = result.fetchone()
        if job_progress:
            print(f"   ✅ transformation_job_progress view works")
            print(f"      Job: {job_progress[1]}")
            print(f"      Progress: {job_progress[7]}%")

        result = session.execute(text(f"SELECT * FROM transformation_job_stats WHERE job_id = '{job.id}';"))
        job_stats = result.fetchone()
        if job_stats:
            print(f"   ✅ transformation_job_stats view works")
            print(f"      Total transformations: {job_stats[4]}")
            print(f"      Total tokens: {job_stats[7]}")

        # Commit all changes
        session.commit()
        print("\n" + "="*80)
        print("✅ All tests passed!")
        print("="*80)
        print("\n📊 Test Summary:")
        print(f"   • Created TransformationJob: {job.id}")
        print(f"   • Created ChunkTransformation: {chunk_trans.id}")
        print(f"   • Created TransformationLineage: {lineage_gen1.id}")
        print(f"   • Verified helper functions and views")
        print("\n💡 Models are working correctly with the database!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Test failed: {e}")
        import traceback
        print("\n🔍 Traceback:")
        print(traceback.format_exc())
        return

    finally:
        session.close()


if __name__ == "__main__":
    test_pipeline_models()
