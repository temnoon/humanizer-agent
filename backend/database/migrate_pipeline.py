#!/usr/bin/env python3
"""
Migration script for transformation pipeline tables.

Adds transformation_jobs, chunk_transformations, and transformation_lineage
tables along with indexes and helper functions.

This migration is IDEMPOTENT - safe to run multiple times.

Usage:
    python migrate_pipeline.py --database-url postgresql://user:pass@localhost/humanizer

Or use environment variable:
    DATABASE_URL=postgresql://user:pass@localhost/humanizer python migrate_pipeline.py
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


def read_migration_file(migration_path: Path) -> str:
    """Read SQL migration file."""
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    with open(migration_path, 'r') as f:
        return f.read()


def check_tables_exist(engine) -> dict:
    """Check which pipeline tables already exist."""
    table_checks = {
        'transformation_jobs': False,
        'chunk_transformations': False,
        'transformation_lineage': False
    }

    with engine.connect() as conn:
        for table in table_checks.keys():
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                );
            """))
            table_checks[table] = result.fetchone()[0]

    return table_checks


def run_migration(database_url: str, force: bool = False):
    """
    Run transformation pipeline migration.

    Args:
        database_url: PostgreSQL connection string
        force: If True, run migration even if tables already exist
    """
    print(f"🔌 Connecting to database...")
    engine = create_engine(database_url, echo=False)

    # Test connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version.split(',')[0]}")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

    # Check if tables already exist
    print("\n🔍 Checking existing tables...")
    existing_tables = check_tables_exist(engine)

    tables_exist = any(existing_tables.values())

    if tables_exist and not force:
        print("\n⚠️  Some pipeline tables already exist:")
        for table, exists in existing_tables.items():
            status = "✅ EXISTS" if exists else "❌ MISSING"
            print(f"   {status}: {table}")

        print("\n💡 Migration is idempotent - safe to run again.")
        response = input("\nContinue with migration? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    elif tables_exist:
        print("   Running migration in FORCE mode (--force)")

    # Read migration file
    migration_path = Path(__file__).parent / "pipeline_migration.sql"
    print(f"\n📄 Reading migration from: {migration_path}")
    migration_sql = read_migration_file(migration_path)

    # Execute migration
    print("\n🔨 Running migration...")
    print("   - Creating tables (transformation_jobs, chunk_transformations, transformation_lineage)")
    print("   - Creating indexes for graph queries")
    print("   - Creating helper functions")
    print("   - Creating views")

    try:
        with engine.begin() as conn:
            # Execute the entire migration file
            conn.execute(text(migration_sql))
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        print("\n🔍 Traceback:")
        print(traceback.format_exc())
        sys.exit(1)

    # Verify tables
    print("\n🔍 Verifying tables...")
    expected_tables = [
        'transformation_jobs',
        'chunk_transformations',
        'transformation_lineage'
    ]

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('transformation_jobs', 'chunk_transformations', 'transformation_lineage')
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
        'get_transformation_lineage',
        'get_transformation_descendants',
        'get_chunk_transformation_graph'
    ]

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_type = 'FUNCTION'
            AND routine_name IN ('get_transformation_lineage', 'get_transformation_descendants', 'get_chunk_transformation_graph')
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
    expected_views = ['transformation_job_progress', 'transformation_job_stats']

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            AND table_name IN ('transformation_job_progress', 'transformation_job_stats')
            ORDER BY table_name;
        """))
        views = [row[0] for row in result]

    for view in expected_views:
        if view in views:
            print(f"  ✅ {view}")
        else:
            print(f"  ❌ {view} - MISSING!")

    # Summary
    print("\n" + "="*80)
    print("🎉 Transformation Pipeline Migration Complete!")
    print("="*80)
    print("\n📊 Migration Summary:")
    print(f"  • 3 new tables: {', '.join(expected_tables)}")
    print(f"  • {len(expected_functions)} helper functions (graph traversal)")
    print(f"  • {len(expected_views)} views (job monitoring)")
    print(f"  • Graph-optimized indexes (ChunkRelationship, Lineage)")
    print("\n💡 Next steps:")
    print("  1. Create pipeline API routes: backend/api/pipeline_routes.py")
    print("  2. Test job creation: POST /api/pipeline/jobs")
    print("  3. Test batch transformation: POST /api/pipeline/transform-batch")
    print("  4. Build frontend UI: frontend/src/TransformationPipeline/")
    print("\n📖 Documentation:")
    print("  - Models: backend/models/pipeline_models.py")
    print("  - Schemas: backend/models/pipeline_schemas.py")
    print("  - Migration SQL: backend/database/pipeline_migration.sql")


def main():
    parser = argparse.ArgumentParser(
        description="Run transformation pipeline migration"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        help="PostgreSQL connection string (or use DATABASE_URL env var)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if tables exist"
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

    # Convert asyncpg URL to psycopg2 for synchronous migration operations
    if '+asyncpg://' in database_url:
        database_url = database_url.replace('+asyncpg://', '+psycopg2://')
        print("🔄 Converted asyncpg URL to psycopg2 for migration")

    # Run migration
    run_migration(database_url, force=args.force)


if __name__ == "__main__":
    main()
