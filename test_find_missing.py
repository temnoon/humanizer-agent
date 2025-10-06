#!/usr/bin/env python3
"""
Test script to find a few missing files and verify the search logic works.
"""

import asyncio
import asyncpg
from pathlib import Path

# Archive locations
CHAT_ARCHIVES = [
    Path("/Users/tem/rho/var/media/chat7"),
    Path("/Users/tem/humanizer_app/nab/chat6"),
    Path("/Users/tem/nab/chat6"),
    Path("/Users/tem/nab2/chat5"),
]

DB_URL = "postgresql://humanizer@localhost/humanizer"


def find_file_in_archives(file_id: str, archives: list) -> Path | None:
    """Search for a file across multiple archive locations."""
    # Clean file ID
    clean_id = file_id.replace('file-service://', '').replace('sediment://', '').replace('file://', '')

    # Search pattern: file-{ID}-*
    pattern = f"{clean_id}-*"

    for archive in archives:
        if not archive.exists():
            print(f"⚠️  Archive not found: {archive}")
            continue

        # Search in root directory
        matches = list(archive.glob(pattern))
        if matches:
            return matches[0]

        # Search in conversation subdirectories (UUID folders)
        for conv_dir in archive.iterdir():
            if conv_dir.is_dir():
                matches = list(conv_dir.glob(pattern))
                if matches:
                    return matches[0]

                # Check subdirectories (like "audio" folder)
                for subdir in conv_dir.iterdir():
                    if subdir.is_dir():
                        matches = list(subdir.glob(pattern))
                        if matches:
                            return matches[0]

    return None


async def test_search():
    """Test searching for a few missing files."""
    conn = await asyncpg.connect(DB_URL)

    # Get 10 missing files
    rows = await conn.fetch("""
        SELECT
            original_media_id,
            original_filename,
            media_type
        FROM media
        WHERE storage_path IS NULL
        LIMIT 10
    """)

    await conn.close()

    print(f"\n=== Testing Search for {len(rows)} Missing Files ===\n")

    found = 0
    not_found = 0

    for row in rows:
        file_id = row['original_media_id']
        filename = row['original_filename']
        media_type = row['media_type']

        print(f"Searching for: {filename}")
        print(f"  File ID: {file_id}")
        print(f"  Type: {media_type}")

        result = find_file_in_archives(file_id, CHAT_ARCHIVES)

        if result:
            print(f"  ✓ FOUND: {result}")
            found += 1
        else:
            print(f"  ✗ NOT FOUND")
            not_found += 1

        print()

    print("=== Summary ===")
    print(f"Found: {found}/{len(rows)}")
    print(f"Not found: {not_found}/{len(rows)}")
    print(f"Success rate: {found/len(rows)*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(test_search())
