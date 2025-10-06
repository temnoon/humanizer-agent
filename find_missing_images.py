#!/usr/bin/env python3
"""
Find missing ChatGPT archive images across multiple archive versions.

Searches chat5, chat6, and chat7 for files that are missing from the database.
"""

import asyncio
import asyncpg
from pathlib import Path
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Archive locations
CHAT_ARCHIVES = [
    Path("/Users/tem/rho/var/media/chat7"),
    Path("/Users/tem/humanizer_app/nab/chat6"),
    Path("/Users/tem/nab/chat6"),
    Path("/Users/tem/nab2/chat5"),
]

# Media storage location
MEDIA_STORAGE = Path("/Users/tem/humanizer-agent/backend/media/chatgpt")

# Database connection
DB_URL = "postgresql://humanizer@localhost/humanizer"


async def get_missing_files():
    """Get list of missing media files from database."""
    conn = await asyncpg.connect(DB_URL)

    rows = await conn.fetch("""
        SELECT
            id,
            collection_id,
            original_media_id,
            original_filename,
            mime_type
        FROM media
        WHERE storage_path IS NULL
        ORDER BY original_media_id
    """)

    await conn.close()

    logger.info(f"Found {len(rows)} missing files in database")
    return rows


def find_file_in_archives(file_id: str, archives: list[Path]) -> Path | None:
    """
    Search for a file across multiple archive locations.

    Files are named: file-{ID}-{original_filename}
    We search for files that START with file-{ID}-
    """
    # Clean file ID
    clean_id = file_id.replace('file-service://', '').replace('sediment://', '').replace('file://', '')

    # Search pattern: file-{ID}-*
    pattern = f"{clean_id}-*"

    for archive in archives:
        if not archive.exists():
            continue

        # Search in root directory
        matches = list(archive.glob(pattern))
        if matches:
            logger.debug(f"Found {clean_id} in {archive}")
            return matches[0]

        # Search in conversation subdirectories (UUID folders)
        for conv_dir in archive.iterdir():
            if conv_dir.is_dir() and len(conv_dir.name) == 36:  # UUID length
                matches = list(conv_dir.glob(pattern))
                if matches:
                    logger.debug(f"Found {clean_id} in {archive}/{conv_dir.name}")
                    return matches[0]

    return None


async def copy_missing_file(media_id: str, collection_id: str, file_path: Path):
    """Copy a found file to the media storage location."""
    # Get file extension
    extension = file_path.suffix

    # Clean the file ID for storage
    clean_id = media_id.replace('file-service://', '').replace('file://', '').replace('/', '_')

    # Storage path: media/chatgpt/{collection_id}/file-{ID}{ext}
    storage_dir = MEDIA_STORAGE / str(collection_id)
    storage_dir.mkdir(parents=True, exist_ok=True)

    storage_filename = f"{clean_id}{extension}"
    storage_path = storage_dir / storage_filename

    # Copy file
    shutil.copy2(file_path, storage_path)
    logger.info(f"Copied {file_path.name} -> {storage_path}")

    return str(storage_path.relative_to(MEDIA_STORAGE.parent))


async def update_database(media_id: str, storage_path: str, file_size: int):
    """Update database with new storage path."""
    conn = await asyncpg.connect(DB_URL)

    # Read file for blob storage (if < 10MB)
    blob_data = None
    full_path = MEDIA_STORAGE.parent / storage_path

    if file_size < 10 * 1024 * 1024:  # < 10MB
        with open(full_path, 'rb') as f:
            blob_data = f.read()

    await conn.execute("""
        UPDATE media
        SET
            storage_path = $1,
            size_bytes = $2,
            blob_data = $3
        WHERE id = $4
    """, storage_path, file_size, blob_data, media_id)

    await conn.close()


async def main():
    """Main recovery process."""
    logger.info("=== ChatGPT Archive Image Recovery ===")

    # Get missing files
    missing_files = await get_missing_files()

    if not missing_files:
        logger.info("No missing files to recover!")
        return

    # Stats
    found_count = 0
    not_found_count = 0
    copied_count = 0

    # Process each missing file
    for row in missing_files:
        media_id = row['id']
        collection_id = row['collection_id']
        original_media_id = row['original_media_id']
        original_filename = row['original_filename']

        # Search for file
        file_path = find_file_in_archives(original_media_id, CHAT_ARCHIVES)

        if file_path:
            found_count += 1
            logger.info(f"✓ Found: {original_filename} ({original_media_id})")

            try:
                # Copy file
                storage_path = await copy_missing_file(original_media_id, collection_id, file_path)
                file_size = file_path.stat().st_size

                # Update database
                await update_database(media_id, storage_path, file_size)
                copied_count += 1

            except Exception as e:
                logger.error(f"Failed to copy {original_filename}: {e}")
        else:
            not_found_count += 1
            logger.debug(f"✗ Not found: {original_filename} ({original_media_id})")

    # Summary
    logger.info("")
    logger.info("=== Summary ===")
    logger.info(f"Total missing files: {len(missing_files)}")
    logger.info(f"Found in archives: {found_count}")
    logger.info(f"Successfully copied: {copied_count}")
    logger.info(f"Still missing: {not_found_count}")
    logger.info(f"Recovery rate: {found_count / len(missing_files) * 100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
