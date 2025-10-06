"""
Apple Photos Integration Service

Provides access to the macOS Photos library using AppleScript.
Requires macOS and Photos.app to be installed.
"""

import subprocess
import os
import platform
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ApplePhotosService:
    """Service for interacting with Apple Photos library on macOS"""

    def __init__(self):
        """Initialize the service and check for macOS"""
        self.is_macos = platform.system() == 'Darwin'
        if not self.is_macos:
            logger.warning("Apple Photos service only works on macOS")

    def is_available(self) -> bool:
        """Check if Apple Photos is available on this system"""
        if not self.is_macos:
            return False

        # Check if Photos.app exists
        photos_app_path = "/System/Applications/Photos.app"
        return os.path.exists(photos_app_path)

    def _run_applescript(self, script: str) -> str:
        """Execute an AppleScript and return the result"""
        if not self.is_macos:
            raise RuntimeError("AppleScript only works on macOS")

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"AppleScript failed: {e.stderr}")
            raise RuntimeError(f"AppleScript error: {e.stderr}")

    def get_albums(self) -> List[Dict[str, str]]:
        """Get list of albums from Photos library"""
        script = '''
        tell application "Photos"
            set albumList to {}
            repeat with anAlbum in albums
                set albumName to name of anAlbum
                set albumCount to count of media items of anAlbum
                set end of albumList to albumName & "|||" & albumCount
            end repeat
            return albumList
        end tell
        '''

        try:
            result = self._run_applescript(script)
            albums = []
            for line in result.split(', '):
                if '|||' in line:
                    parts = line.split('|||')
                    albums.append({
                        'name': parts[0],
                        'count': int(parts[1]) if len(parts) > 1 else 0
                    })
            return albums
        except Exception as e:
            logger.error(f"Failed to get albums: {e}")
            return []

    def export_album(
        self,
        album_name: str,
        export_path: str,
        limit: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Export photos from an album to a folder

        Args:
            album_name: Name of the album to export
            export_path: Path to export photos to
            limit: Maximum number of photos to export (None = all)

        Returns:
            Dictionary with export stats
        """
        # Create export directory if it doesn't exist
        Path(export_path).mkdir(parents=True, exist_ok=True)

        limit_clause = f" 1 thru {limit}" if limit else ""

        script = f'''
        tell application "Photos"
            set targetAlbum to album "{album_name}"
            set photoCount to count of media items of targetAlbum
            set exportedCount to 0

            set photoList to media items{limit_clause} of targetAlbum

            repeat with aPhoto in photoList
                try
                    set photoFilename to filename of aPhoto
                    export {{aPhoto}} to POSIX file "{export_path}"
                    set exportedCount to exportedCount + 1
                end try
            end repeat

            return "Exported " & exportedCount & " of " & photoCount & " photos"
        end tell
        '''

        try:
            result = self._run_applescript(script)
            logger.info(f"Export result: {result}")

            # Count exported files
            exported_files = list(Path(export_path).glob("*"))

            return {
                "status": "success",
                "message": result,
                "export_path": export_path,
                "files_exported": len(exported_files)
            }

        except Exception as e:
            logger.error(f"Failed to export album: {e}")
            return {
                "status": "error",
                "message": str(e),
                "export_path": export_path,
                "files_exported": 0
            }

    def export_recent(
        self,
        export_path: str,
        days: int = 30,
        limit: Optional[int] = 100
    ) -> Dict[str, any]:
        """
        Export recent photos from the library

        Args:
            export_path: Path to export photos to
            days: Number of days back to search
            limit: Maximum number of photos to export

        Returns:
            Dictionary with export stats
        """
        # Create export directory if it doesn't exist
        Path(export_path).mkdir(parents=True, exist_ok=True)

        script = f'''
        tell application "Photos"
            set today to current date
            set cutoffDate to today - ({days} * days)

            set recentPhotos to {{}}
            repeat with aPhoto in media items of library
                if date of aPhoto > cutoffDate then
                    set end of recentPhotos to aPhoto
                end if
            end repeat

            set exportedCount to 0

            -- Limit to requested number of photos
            set maxPhotos to {limit or 100}
            if (count of recentPhotos) > maxPhotos then
                set photoList to items 1 thru maxPhotos of recentPhotos
            else
                set photoList to recentPhotos
            end if

            repeat with aPhoto in photoList
                try
                    export {{aPhoto}} to POSIX file "{export_path}"
                    set exportedCount to exportedCount + 1
                end try
            end repeat

            return "Exported " & exportedCount & " recent photos"
        end tell
        '''

        try:
            result = self._run_applescript(script)
            logger.info(f"Export result: {result}")

            # Count exported files
            exported_files = list(Path(export_path).glob("*"))

            return {
                "status": "success",
                "message": result,
                "export_path": export_path,
                "files_exported": len(exported_files),
                "days": days
            }

        except Exception as e:
            logger.error(f"Failed to export recent photos: {e}")
            return {
                "status": "error",
                "message": str(e),
                "export_path": export_path,
                "files_exported": 0
            }

    def get_photo_count(self) -> int:
        """Get total number of photos in the library"""
        script = '''
        tell application "Photos"
            return count of media items
        end tell
        '''

        try:
            result = self._run_applescript(script)
            return int(result)
        except Exception as e:
            logger.error(f"Failed to get photo count: {e}")
            return 0
