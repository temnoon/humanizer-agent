#!/usr/bin/env python3
"""
Recover missing ChatGPT images by matching FILENAMES across archive versions.

The issue: File IDs change between ChatGPT exports, but filenames stay the same.
Solution: Match by original_filename instead of file ID.
"""

import asyncio
import asyncpg
from pathlib import Path
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
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


def build_filename_index(archives: list[Path]) -> dict:
    """
    Build an index of all files in archives by filename.

    Returns: {filename: file_path}
    """
    logger.info("Building filename index from archives...")

    filename_index = {}

    for archive in archives:
        if not archive.exists():
            logger.warning(f"Archive not found: {archive}")
            continue

        logger.info(f"Scanning: {archive}")

        # Scan root directory
        for file_path in archive.glob("file-*"):
            if file_path.is_file():
                # Extract original filename from: file-{ID}-{filename}
                parts = file_path.name.split('-', 2)  # Split on first 2 dashes
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

    logger.info(f"Indexed {len(filename_index)} unique filenames")
    return filename_index


async def get_missing_files():
    """Get list of missing media files from database."""
    conn = await asyncpg.connect(DB_URL)

    # Only get images (documents like PDFs are not in archives)
    rows = await conn.fetch("""
        SELECT
            id,
            collection_id,
            original_media_id,
            original_filename,
            mime_type,
            media_type
        FROM media
        WHERE storage_path IS NULL
          AND media_type = 'image'
        ORDER BY original_filename
    """)

    await conn.close()

    logger.info(f"Found {len(rows)} missing images in database")
    return rows


async def copy_file_to_storage(media_row, file_path: Path):
    """Copy a found file to the media storage location and update database."""
    media_id = media_row['id']
    collection_id = media_row['collection_id']
    original_media_id = media_row['original_media_id']

    # Get file extension
    extension = file_path.suffix

    # Clean the file ID for storage
    clean_id = original_media_id.replace('file-service://', '').replace('file://', '').replace('/', '_')

    # Storage path: media/chatgpt/{collection_id}/file-{ID}{ext}
    storage_dir = MEDIA_STORAGE / str(collection_id)
    storage_dir.mkdir(parents=True, exist_ok=True)

    storage_filename = f"{clean_id}{extension}"
    storage_path = storage_dir / storage_filename

    # Copy file
    shutil.copy2(file_path, storage_path)

    # Get file size
    file_size = storage_path.stat().st_size

    # Read file for blob storage (if < 10MB)
    blob_data = None
    if file_size < 10 * 1024 * 1024:
        with open(storage_path, 'rb') as f:
            blob_data = f.read()

    # Update database
    conn = await asyncpg.connect(DB_URL)

    relative_storage_path = str(storage_path.relative_to(MEDIA_STORAGE.parent))

    await conn.execute("""
        UPDATE media
        SET
            storage_path = $1,
            size_bytes = $2,
            blob_data = $3
        WHERE id = $4::uuid
    """, relative_storage_path, file_size, blob_data, str(media_id))

    await conn.close()

    return relative_storage_path


async def main():
    """Main recovery process."""
    logger.info("=== ChatGPT Image Recovery (by Filename Matching) ===\n")

    # Build filename index from all archives
    filename_index = build_filename_index(CHAT_ARCHIVES)

    if not filename_index:
        logger.error("No files found in archives!")
        return

    logger.info("")

    # Get missing files
    missing_files = await get_missing_files()

    if not missing_files:
        logger.info("No missing images to recover!")
        return

    logger.info("")

    # Stats
    found_count = 0
    copied_count = 0
    failed_count = 0
    not_found = []

    # Process each missing file
    for row in missing_files:
        original_filename = row['original_filename']

        # Look up filename in index
        if original_filename in filename_index:
            file_path = filename_index[original_filename]
            found_count += 1

            try:
                storage_path = await copy_file_to_storage(row, file_path)
                logger.info(f"✓ Recovered: {original_filename}")
                logger.info(f"    From: {file_path}")
                logger.info(f"    To: {storage_path}")
                copied_count += 1

            except Exception as e:
                logger.error(f"✗ Failed to copy {original_filename}: {e}")
                failed_count += 1
        else:
            not_found.append(original_filename)

    # Summary
    logger.info("")
    logger.info("=== Summary ===")
    logger.info(f"Total missing images: {len(missing_files)}")
    logger.info(f"Found in archives: {found_count}")
    logger.info(f"Successfully recovered: {copied_count}")
    logger.info(f"Failed to copy: {failed_count}")
    logger.info(f"Still missing: {len(not_found)}")
    logger.info(f"Recovery rate: {found_count / len(missing_files) * 100:.1f}%")

    # Show sample of files still missing
    if not_found:
        logger.info("")
        logger.info(f"Sample of files still missing (first 10):")
        for filename in not_found[:10]:
            logger.info(f"  - {filename}")


if __name__ == "__main__":
    asyncio.run(main())
