#!/usr/bin/env python3
"""
Dry run of image recovery to see how many we can recover WITHOUT making changes.
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


def build_filename_index(archives: list) -> dict:
    """Build an index of all files in archives by filename."""
    print("Building filename index from archives...")

    filename_index = {}

    for archive in archives:
        if not archive.exists():
            print(f"  ⚠️  Archive not found: {archive}")
            continue

        print(f"  Scanning: {archive.name}")

        # Scan root directory
        for file_path in archive.glob("file-*"):
            if file_path.is_file():
                parts = file_path.name.split('-', 2)
                if len(parts) >= 3:
                    original_filename = parts[2]
                    if original_filename not in filename_index:
                        filename_index[original_filename] = file_path

        # Scan conversation subdirectories
        for conv_dir in archive.iterdir():
            if conv_dir.is_dir():
                for file_path in conv_dir.rglob("file-*"):
                    if file_path.is_file():
                        parts = file_path.name.split('-', 2)
                        if len(parts) >= 3:
                            original_filename = parts[2]
                            if original_filename not in filename_index:
                                filename_index[original_filename] = file_path

    print(f"  Indexed {len(filename_index)} unique filenames\n")
    return filename_index


async def main():
    """Dry run to estimate recovery success."""
    print("=== Image Recovery Dry Run ===\n")

    # Build filename index
    filename_index = build_filename_index(CHAT_ARCHIVES)

    # Get missing images
    conn = await asyncpg.connect(DB_URL)

    missing_images = await conn.fetch("""
        SELECT
            original_filename,
            media_type
        FROM media
        WHERE storage_path IS NULL
          AND media_type = 'image'
    """)

    total_missing = await conn.fetchval("""
        SELECT COUNT(*)
        FROM media
        WHERE storage_path IS NULL
    """)

    await conn.close()

    # Check how many we can recover
    can_recover = 0
    cannot_recover = 0
    sample_recoverable = []
    sample_not_recoverable = []

    for row in missing_images:
        filename = row['original_filename']

        if filename in filename_index:
            can_recover += 1
            if len(sample_recoverable) < 5:
                sample_recoverable.append(filename)
        else:
            cannot_recover += 1
            if len(sample_not_recoverable) < 5:
                sample_not_recoverable.append(filename)

    # Report
    print("=== Results ===\n")
    print(f"Total missing media: {total_missing}")
    print(f"Missing images: {len(missing_images)}")
    print(f"  Can recover: {can_recover} ({can_recover/len(missing_images)*100:.1f}%)")
    print(f"  Cannot recover: {cannot_recover} ({cannot_recover/len(missing_images)*100:.1f}%)")

    print(f"\nSample recoverable:")
    for filename in sample_recoverable:
        print(f"  ✓ {filename}")

    print(f"\nSample NOT recoverable:")
    for filename in sample_not_recoverable:
        print(f"  ✗ {filename}")

    print(f"\nReady to recover {can_recover} images!")
    print("Run recover_images_by_filename.py to execute recovery.")


if __name__ == "__main__":
    asyncio.run(main())
