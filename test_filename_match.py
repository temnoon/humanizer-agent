#!/usr/bin/env python3
"""
Test filename-based matching to verify recovery logic.
"""

from pathlib import Path

CHAT_ARCHIVES = [
    Path("/Users/tem/rho/var/media/chat7"),
    Path("/Users/tem/humanizer_app/nab/chat6"),
    Path("/Users/tem/nab/chat6"),
    Path("/Users/tem/nab2/chat5"),
]


def build_filename_index_sample(archives: list) -> dict:
    """Build index of first 1000 files for testing."""
    filename_index = {}
    total_files = 0

    for archive in archives:
        if not archive.exists():
            print(f"⚠️  Archive not found: {archive}")
            continue

        print(f"Scanning: {archive.name}")

        # Scan root directory
        for file_path in archive.glob("file-*"):
            if file_path.is_file():
                total_files += 1
                # Extract filename from: file-{ID}-{filename}
                parts = file_path.name.split('-', 2)
                if len(parts) >= 3:
                    original_filename = parts[2]
                    if original_filename not in filename_index:
                        filename_index[original_filename] = file_path

                if total_files >= 1000:  # Sample first 1000
                    break

        if total_files >= 1000:
            break

    return filename_index


# Test
print("=== Testing Filename Matching ===\n")

index = build_filename_index_sample(CHAT_ARCHIVES)
print(f"\nIndexed {len(index)} unique filenames\n")

# Test with known file
test_filename = "IMG_6499.jpeg"
print(f"Looking for: {test_filename}")

if test_filename in index:
    print(f"✓ FOUND: {index[test_filename]}")
else:
    print("✗ NOT FOUND")

print("\nSample of indexed files:")
for i, (filename, path) in enumerate(list(index.items())[:10]):
    print(f"  {filename} -> {path.name}")
