"""
ChatGPT Archive Parser Service

Parses ChatGPT export archives in various formats:
- conversations.json (tree structure with mapping)
- Media files (images, audio, documents)
- Multiple archive format versions (2024-2025)
"""

import json
import logging
import mimetypes
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class ChatGPTArchiveParser:
    """Parse ChatGPT export archives and extract conversations with media."""

    def __init__(self, archive_path: Path):
        """
        Initialize parser with archive path.

        Args:
            archive_path: Path to extracted ChatGPT archive folder
        """
        self.archive_path = Path(archive_path)
        self.conversations_file = self.archive_path / "conversations.json"
        self.media_cache: Dict[str, Path] = {}

        if not self.archive_path.exists():
            raise FileNotFoundError(f"Archive path not found: {archive_path}")

    def scan_media_files(self) -> Dict[str, Path]:
        """
        Scan archive for all media files across different format versions.

        ChatGPT archive formats:
        - User uploads (top level): file-<hash>-<suffix>.<ext>
        - New style (user-*/): file_<hash>-<uuid>.<ext>
        - DALL-E: dalle-generations/file-<hash>-<uuid>.webp
        - UUID folders: <uuid>/audio/file_<hash>.wav
        - DAT format: file_<hash>.dat (late 2025)

        Returns:
            Dictionary mapping file identifiers (original IDs) to file paths
        """
        media_files = {}

        # Pattern 1: Top-level user uploads (file-<hash>-<suffix>.<ext>)
        logger.info("Scanning top-level user uploads...")
        for file_path in self.archive_path.glob("file-*"):
            if file_path.is_file():
                # Extract original file ID (before first dash)
                # Example: file-WrEi4rvcrFhxPWx6q6KqSVv1-9C636106... -> file-WrEi4rvcrFhxPWx6q6KqSVv1
                filename = file_path.name
                if '-' in filename:
                    # Get file ID portion (file-HASH)
                    parts = filename.split('-')
                    if len(parts) >= 2:
                        original_id = f"{parts[0]}-{parts[1]}"  # file-HASH
                        media_files[original_id] = file_path
                        # Also store by full filename for fallback
                        media_files[filename] = file_path

        # Pattern 2: New style images in user-* folders (file_<hash>-<uuid>.<ext>)
        logger.info("Scanning user-* folders...")
        for user_folder in self.archive_path.glob("user-*"):
            if user_folder.is_dir():
                for file_path in user_folder.glob("file_*"):
                    # Extract original file ID
                    # Example: file_0000000001e851f7b96c57ab1fbc0a9c-86b9a53b... -> file-0000000001e851f7b96c57ab1fbc0a9c
                    filename = file_path.name
                    if '-' in filename and filename.startswith('file_'):
                        # Convert file_ to file- and extract hash
                        hash_part = filename[5:].split('-')[0]  # Remove 'file_', get hash before first dash
                        original_id = f"file-{hash_part}"
                        media_files[original_id] = file_path
                        # Also store by full filename
                        media_files[filename] = file_path

        # Pattern 3: DALL-E generations (file-<hash>-<uuid>.webp)
        dalle_folder = self.archive_path / "dalle-generations"
        if dalle_folder.exists():
            logger.info("Scanning DALL-E generations...")
            for file_path in dalle_folder.glob("file-*"):
                if file_path.is_file():
                    # Extract original file ID
                    filename = file_path.name
                    if '-' in filename:
                        parts = filename.split('-')
                        if len(parts) >= 2:
                            original_id = f"{parts[0]}-{parts[1]}"  # file-HASH
                            media_files[original_id] = file_path
                            media_files[filename] = file_path

        # Pattern 4: UUID folders with audio subfolders
        for folder in self.archive_path.iterdir():
            if folder.is_dir() and len(folder.name) == 36:  # UUID length
                audio_folder = folder / "audio"
                if audio_folder.exists():
                    for audio_file in audio_folder.glob("file_*"):
                        filename = audio_file.name
                        if '-' in filename and filename.startswith('file_'):
                            hash_part = filename[5:].split('-')[0]
                            original_id = f"file-{hash_part}"
                            media_files[original_id] = audio_file
                            media_files[filename] = audio_file

        # Pattern 5: .dat files (latest format)
        for dat_file in self.archive_path.glob("*.dat"):
            media_files[dat_file.name] = dat_file

        logger.info(f"Found {len(media_files)} media file mappings")
        self.media_cache = media_files
        return media_files

    def load_conversations(self) -> List[Dict]:
        """
        Load conversations from conversations.json.

        Returns:
            List of conversation objects
        """
        if not self.conversations_file.exists():
            raise FileNotFoundError(f"conversations.json not found in {self.archive_path}")

        with open(self.conversations_file, 'r', encoding='utf-8') as f:
            conversations = json.load(f)

        if isinstance(conversations, list):
            return conversations
        elif isinstance(conversations, dict) and 'conversations' in conversations:
            return conversations['conversations']
        else:
            logger.warning("Unexpected conversations.json format")
            return []

    def parse_conversation(self, conversation: Dict) -> Tuple[Dict, List[Dict], List[str]]:
        """
        Parse a single conversation into structured format.

        Args:
            conversation: Raw conversation object from conversations.json

        Returns:
            Tuple of (metadata, messages, media_references)
        """
        # Extract metadata
        metadata = {
            'title': conversation.get('title', 'Untitled'),
            'create_time': conversation.get('create_time'),
            'update_time': conversation.get('update_time'),
            'conversation_id': conversation.get('id'),
            'model_slug': conversation.get('model_slug'),
            'default_model_slug': conversation.get('default_model_slug'),
            'gizmo_id': conversation.get('gizmo_id'),  # Custom GPT identifier
            'safe_mode': conversation.get('safe_mode'),
            'conversation_template_id': conversation.get('conversation_template_id')
        }

        # Parse message tree
        mapping = conversation.get('mapping', {})
        messages = []
        media_references = []

        # Build message tree by traversing from root
        if not mapping:
            logger.warning(f"Conversation {metadata['conversation_id']} has no mapping")
            return metadata, messages, media_references

        # Find root node (node with no parent or parent is None)
        root_nodes = [node_id for node_id, node in mapping.items()
                      if node.get('parent') is None or node.get('parent') == '']

        if not root_nodes:
            # Fallback: use current_node if specified
            current_node = conversation.get('current_node')
            if current_node:
                root_nodes = [current_node]
            else:
                logger.warning(f"No root node found for conversation {metadata['conversation_id']}")
                return metadata, messages, media_references

        # Traverse tree depth-first
        def traverse_node(node_id: str, depth: int = 0, sequence: int = 0):
            nonlocal messages, media_references

            if node_id not in mapping:
                return sequence

            node = mapping[node_id]
            message_data = node.get('message')

            if message_data and message_data.get('content'):
                # Extract message details
                author = message_data.get('author', {})
                content = message_data.get('content', {})
                metadata_field = message_data.get('metadata', {})

                # Parse content parts
                parts = content.get('parts', [])
                if parts:
                    content_text = ' '.join([
                        part if isinstance(part, str) else str(part)
                        for part in parts
                    ])
                else:
                    content_text = ''

                # Extract media references from content
                if 'image_asset_pointer' in str(content):
                    # Extract image pointer
                    for part in parts:
                        if isinstance(part, dict) and 'asset_pointer' in part:
                            media_references.append(part['asset_pointer'])

                # Extract media from metadata attachments
                attachments = metadata_field.get('attachments', [])
                for attachment in attachments:
                    if isinstance(attachment, dict):
                        # Various attachment structures
                        if 'id' in attachment:
                            media_references.append(attachment['id'])
                        if 'file_id' in attachment:
                            media_references.append(attachment['file_id'])

                # SPECIAL: Tool messages may have image references in content
                # Extract sediment:// and dalle image references from tool message content
                if author.get('role') == 'tool' and content_text:
                    # Pattern 1: sediment://file_HASH (DALL-E 3+ generations)
                    import re
                    sediment_matches = re.findall(r'sediment://file_([a-zA-Z0-9]+)', content_text)
                    for hash_part in sediment_matches:
                        # Convert to standard file- format and add to references
                        file_id = f'file-{hash_part}'
                        media_references.append(file_id)
                        # Also create synthetic attachment for frontend display
                        if not attachments:
                            attachments = []
                        attachments.append({
                            'id': file_id,
                            'mimeType': 'image/webp',  # DALL-E generates webp
                            'name': f'DALL-E_{hash_part[:12]}.webp'
                        })

                    # Pattern 2: file-service://file-HASH (older DALL-E)
                    service_matches = re.findall(r'file-service://([a-zA-Z0-9-]+)', content_text)
                    for file_id in service_matches:
                        media_references.append(file_id)
                        if not attachments:
                            attachments = []
                        if file_id not in [att.get('id') for att in attachments]:
                            attachments.append({
                                'id': file_id,
                                'mimeType': 'image/webp',
                                'name': f'generated_{file_id[:16]}.webp'
                            })

                # Update metadata with synthetic attachments for tool messages
                if attachments:
                    metadata_field['attachments'] = attachments

                # Build message object
                message = {
                    'node_id': node_id,
                    'sequence_number': sequence,
                    'role': author.get('role', 'unknown'),
                    'author_name': author.get('name'),
                    'content': content_text,
                    'content_type': content.get('content_type', 'text'),
                    'create_time': message_data.get('create_time'),
                    'update_time': message_data.get('update_time'),
                    'status': message_data.get('status'),
                    'weight': message_data.get('weight', 1.0),
                    'metadata': metadata_field,
                    'end_turn': message_data.get('end_turn'),
                    'recipient': message_data.get('recipient', 'all')
                }

                messages.append(message)
                sequence += 1

            # Traverse children
            children = node.get('children', [])
            for child_id in children:
                sequence = traverse_node(child_id, depth + 1, sequence)

            return sequence

        # Start traversal from all root nodes
        for root_id in root_nodes:
            traverse_node(root_id, 0, len(messages))

        return metadata, messages, media_references

    def find_media_file(self, reference: str) -> Optional[Path]:
        """
        Find media file by reference.

        Handles various reference formats:
        - file-HASH (standard)
        - sediment://file_HASH (DALL-E 3+, converts to file-HASH)
        - file-service://file-HASH (older format)

        Args:
            reference: Media file reference (file ID, pointer, etc.)

        Returns:
            Path to media file, or None if not found
        """
        # Clean up reference
        clean_ref = reference.replace('sediment://', '').replace('file-service://', '').replace('file://', '')

        # Try exact match
        if clean_ref in self.media_cache:
            return self.media_cache[clean_ref]

        # Convert file_ to file- for sediment:// references
        if clean_ref.startswith('file_'):
            file_dash = 'file-' + clean_ref[5:]  # Replace file_ with file-
            if file_dash in self.media_cache:
                return self.media_cache[file_dash]

        # Try with file- prefix if not present
        if not clean_ref.startswith('file-') and not clean_ref.startswith('file_'):
            prefixed = f"file-{clean_ref}"
            if prefixed in self.media_cache:
                return self.media_cache[prefixed]

        # Try with file_ prefix
        underscore_prefixed = f"file_{clean_ref}"
        if underscore_prefixed in self.media_cache:
            return self.media_cache[underscore_prefixed]

        # Try partial match (contains reference)
        for key, path in self.media_cache.items():
            if clean_ref in key or reference in key:
                return path

        logger.debug(f"Media file not found for reference: {reference}")
        return None

    def detect_media_type(self, file_path: Path) -> Tuple[str, str]:
        """
        Detect media type and MIME type from file.

        Args:
            file_path: Path to media file

        Returns:
            Tuple of (media_type, mime_type)
        """
        # Try MIME type detection
        mime_type, _ = mimetypes.guess_type(str(file_path))

        # For .dat files, try to detect by magic bytes
        if file_path.suffix == '.dat' or not mime_type:
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(16)

                # Check magic bytes
                if header.startswith(b'\x89PNG'):
                    mime_type = 'image/png'
                elif header.startswith(b'\xff\xd8\xff'):
                    mime_type = 'image/jpeg'
                elif header.startswith(b'RIFF') and b'WEBP' in header:
                    mime_type = 'image/webp'
                elif header.startswith(b'RIFF') and b'WAVE' in header:
                    mime_type = 'audio/wav'
                elif header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
                    mime_type = 'audio/mpeg'
            except Exception as e:
                logger.warning(f"Failed to read magic bytes from {file_path}: {e}")

        # Determine media type category
        if mime_type:
            if mime_type.startswith('image/'):
                media_type = 'image'
            elif mime_type.startswith('audio/'):
                media_type = 'audio'
            elif mime_type.startswith('video/'):
                media_type = 'video'
            else:
                media_type = 'document'
        else:
            media_type = 'unknown'
            mime_type = 'application/octet-stream'

        return media_type, mime_type

    def parse_archive(self) -> Dict[str, Any]:
        """
        Parse entire archive.

        Returns:
            Dictionary with parsed data:
            {
                'conversations': List of conversation metadata,
                'messages': List of all messages across conversations,
                'media_files': Dict of media file paths,
                'stats': Statistics about the archive
            }
        """
        logger.info(f"Parsing ChatGPT archive: {self.archive_path}")

        # Scan for media files
        self.scan_media_files()

        # Load conversations
        conversations_raw = self.load_conversations()

        # Parse each conversation
        parsed_conversations = []
        all_messages = []
        all_media_refs = set()

        for conv in conversations_raw:
            metadata, messages, media_refs = self.parse_conversation(conv)
            parsed_conversations.append({
                'metadata': metadata,
                'message_count': len(messages)
            })
            all_messages.extend(messages)
            all_media_refs.update(media_refs)

        stats = {
            'total_conversations': len(parsed_conversations),
            'total_messages': len(all_messages),
            'total_media_references': len(all_media_refs),
            'total_media_files': len(self.media_cache),
            'archive_path': str(self.archive_path)
        }

        logger.info(f"Parsed {stats['total_conversations']} conversations, "
                   f"{stats['total_messages']} messages, "
                   f"{stats['total_media_files']} media files")

        return {
            'conversations': parsed_conversations,
            'raw_conversations': conversations_raw,
            'media_cache': self.media_cache,
            'media_references': list(all_media_refs),
            'stats': stats
        }
