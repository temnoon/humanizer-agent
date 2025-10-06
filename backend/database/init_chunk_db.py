#!/usr/bin/env python3
"""
Initialize the chunk-based database schema.

This script creates all tables, indexes, triggers, and helper functions
for the new chunk-based architecture.

Usage:
    python init_chunk_db.py --database-url postgresql://user:pass@localhost/humanizer

Or use environment variable:
    DATABASE_URL=postgresql://user:pass@localhost/humanizer python init_chunk_db.py
"""

import argparse
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


def read_schema_file(schema_path: Path) -> str:
    """Read SQL schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r') as f:
        return f.read()


def init_database(database_url: str, drop_existing: bool = False):
    """
    Initialize chunk-based database schema.

    Args:
        database_url: PostgreSQL connection string
        drop_existing: If True, drop existing tables before creating (DANGEROUS!)
    """
    print(f"🔌 Connecting to database...")
    engine = create_engine(database_url, echo=False)

    # Test connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

    # Drop existing tables if requested
    if drop_existing:
        print("\n⚠️  WARNING: Dropping existing chunk-based tables...")
        response = input("Are you sure? This will delete all data! (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

        drop_sql = """
        DROP TABLE IF EXISTS chunk_relationships CASCADE;
        DROP TABLE IF EXISTS chunks CASCADE;
        DROP TABLE IF EXISTS messages CASCADE;
        DROP TABLE IF EXISTS media CASCADE;
        DROP TABLE IF EXISTS collections CASCADE;
        DROP TABLE IF EXISTS belief_frameworks CASCADE;
        DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
        DROP FUNCTION IF EXISTS increment_collection_message_count() CASCADE;
        DROP FUNCTION IF EXISTS increment_message_chunk_count() CASCADE;
        DROP FUNCTION IF EXISTS increment_collection_media_count() CASCADE;
        DROP FUNCTION IF EXISTS find_similar_chunks(vector, float, integer, UUID, UUID[], TEXT) CASCADE;
        DROP FUNCTION IF EXISTS get_message_chunk_hierarchy(UUID) CASCADE;
        DROP FUNCTION IF EXISTS get_collection_summary(UUID) CASCADE;
        DROP FUNCTION IF EXISTS archive_media(UUID, TEXT) CASCADE;
        DROP FUNCTION IF EXISTS get_related_chunks(UUID, TEXT[], INTEGER) CASCADE;
        DROP VIEW IF EXISTS collections_enriched CASCADE;
        DROP VIEW IF EXISTS message_summaries CASCADE;
        """

        try:
            with engine.begin() as conn:
                conn.execute(text(drop_sql))
            print("✅ Dropped existing tables")
        except Exception as e:
            print(f"⚠️  Warning during drop: {e}")

    # Read schema file
    schema_path = Path(__file__).parent / "chunk_schema.sql"
    print(f"\n📄 Reading schema from: {schema_path}")
    schema_sql = read_schema_file(schema_path)

    # Execute schema
    print("\n🔨 Creating tables, indexes, triggers, and functions...")
    try:
        with engine.begin() as conn:
            # Execute the entire schema file
            conn.execute(text(schema_sql))
        print("✅ Schema created successfully!")
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        sys.exit(1)

    # Verify tables
    print("\n🔍 Verifying tables...")
    expected_tables = [
        'collections',
        'messages',
        'chunks',
        'chunk_relationships',
        'media',
        'belief_frameworks'
    ]

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('collections', 'messages', 'chunks', 'chunk_relationships', 'media', 'belief_frameworks')
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]

    for table in expected_tables:
        if table in tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} - MISSING!")

    # Verify functions
    print("\n🔍 Verifying helper functions...")
    expected_functions = [
        'find_similar_chunks',
        'get_message_chunk_hierarchy',
        'get_collection_summary',
        'archive_media',
        'get_related_chunks'
    ]

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_type = 'FUNCTION'
            AND routine_name IN ('find_similar_chunks', 'get_message_chunk_hierarchy', 'get_collection_summary', 'archive_media', 'get_related_chunks')
            ORDER BY routine_name;
        """))
        functions = [row[0] for row in result]

    for func in expected_functions:
        if func in functions:
            print(f"  ✅ {func}")
        else:
            print(f"  ❌ {func} - MISSING!")

    # Verify views
    print("\n🔍 Verifying views...")
    expected_views = ['collections_enriched', 'message_summaries']

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            AND table_name IN ('collections_enriched', 'message_summaries')
            ORDER BY table_name;
        """))
        views = [row[0] for row in result]

    for view in expected_views:
        if view in views:
            print(f"  ✅ {view}")
        else:
            print(f"  ❌ {view} - MISSING!")

    print("\n" + "="*80)
    print("🎉 Database initialization complete!")
    print("="*80)
    print("\n📊 Schema Summary:")
    print(f"  • 6 core tables: {', '.join(expected_tables)}")
    print(f"  • {len(expected_functions)} helper functions")
    print(f"  • {len(expected_views)} views")
    print(f"  • Vector search enabled (pgvector)")
    print(f"  • Full-text search enabled")
    print("\n💡 Next steps:")
    print("  1. Test embedding generation: python -m backend.services.embedding_service")
    print("  2. Import ChatGPT data: python -m backend.services.chatgpt_importer --file conversations.json")
    print("  3. Test semantic search: python -m backend.services.search_service")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize chunk-based database schema"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        help="PostgreSQL connection string (or use DATABASE_URL env var)"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing tables before creating (DANGEROUS!)"
    )

    args = parser.parse_args()

    # Get database URL
    database_url = args.database_url or os.getenv("DATABASE_URL")

    if not database_url:
        # Try to get from settings
        try:
            database_url = settings.database_url
        except Exception:
            pass

    if not database_url:
        print("❌ Error: DATABASE_URL not specified")
        print("\nProvide database URL via:")
        print("  1. --database-url argument")
        print("  2. DATABASE_URL environment variable")
        print("  3. .env file in backend directory")
        sys.exit(1)

    # Validate it's PostgreSQL
    if not database_url.startswith(('postgresql://', 'postgres://', 'postgresql+asyncpg://', 'postgresql+psycopg2://')):
        print(f"❌ Error: Must be a PostgreSQL database URL")
        print(f"   Got: {database_url}")
        sys.exit(1)

    # Convert asyncpg URL to psycopg2 for synchronous schema operations
    if '+asyncpg://' in database_url:
        database_url = database_url.replace('+asyncpg://', '+psycopg2://')

    # Initialize
    init_database(database_url, drop_existing=args.drop_existing)


if __name__ == "__main__":
    main()
