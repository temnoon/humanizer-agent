"""
ChatGPT Archive Importer Service

Imports parsed ChatGPT archives into PostgreSQL with chunk-based storage.
Handles batch processing, media storage, and queues embeddings for generation.
"""

import asyncio
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from models.chunk_models import Collection, Message, Chunk, Media
from services.chatgpt_parser import ChatGPTArchiveParser

logger = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """
    Sanitize text for PostgreSQL storage.

    Removes null bytes and other problematic characters that PostgreSQL
    doesn't allow in UTF-8 text fields.

    Args:
        text: Raw text string

    Returns:
        Sanitized text safe for PostgreSQL
    """
    if not text:
        return text

    # Remove null bytes (0x00)
    text = text.replace('\x00', '')

    # Remove other control characters that might cause issues (optional)
    # Keep newlines, tabs, and carriage returns
    sanitized = ''.join(
        char for char in text
        if char == '\n' or char == '\r' or char == '\t' or ord(char) >= 32 or ord(char) == 0x0A or ord(char) == 0x0D
    )

    return sanitized


class ChatGPTImporter:
    """Import ChatGPT archives into PostgreSQL chunk-based schema."""

    def __init__(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        media_storage_path: Optional[Path] = None
    ):
        """
        Initialize importer.

        Args:
            db_session: Database session
            user_id: User ID for ownership
            media_storage_path: Where to store media files (default: ./media/chatgpt)
        """
        self.db = db_session
        self.user_id = user_id
        self.media_storage_path = media_storage_path or Path("./media/chatgpt")
        self.media_storage_path.mkdir(parents=True, exist_ok=True)

    async def import_archive(
        self,
        archive_path: Path,
        generate_embeddings: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Import entire ChatGPT archive.

        Args:
            archive_path: Path to extracted archive folder
            generate_embeddings: Whether to queue embeddings for generation
            progress_callback: Optional callback for progress updates

        Returns:
            Import statistics
        """
        logger.info(f"Starting ChatGPT archive import from: {archive_path}")

        # Parse archive
        parser = ChatGPTArchiveParser(archive_path)
        parsed_data = parser.parse_archive()

        stats = {
            'conversations_imported': 0,
            'messages_imported': 0,
            'chunks_created': 0,
            'media_imported': 0,
            'embeddings_queued': 0,
            'errors': []
        }

        # Import each conversation
        total_conversations = len(parsed_data['raw_conversations'])
        for idx, conversation in enumerate(parsed_data['raw_conversations']):
            try:
                if progress_callback:
                    progress_callback(idx + 1, total_conversations, conversation.get('title', 'Untitled'))

                result = await self.import_conversation(
                    conversation,
                    parser,
                    generate_embeddings=generate_embeddings
                )

                stats['conversations_imported'] += 1
                stats['messages_imported'] += result['messages']
                stats['chunks_created'] += result['chunks']
                stats['media_imported'] += result['media']
                stats['embeddings_queued'] += result['embeddings_queued']

            except Exception as e:
                error_msg = f"Failed to import conversation {conversation.get('id')}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                stats['errors'].append(error_msg)

        await self.db.commit()

        logger.info(f"Import complete: {stats}")
        return stats

    async def import_conversation(
        self,
        conversation: Dict,
        parser: ChatGPTArchiveParser,
        generate_embeddings: bool = True
    ) -> Dict[str, int]:
        """
        Import a single conversation.

        Args:
            conversation: Raw conversation object
            parser: Parser instance for media lookup
            generate_embeddings: Whether to queue embeddings

        Returns:
            Import statistics for this conversation
        """
        # Parse conversation
        metadata, messages, media_refs = parser.parse_conversation(conversation)

        # Create collection
        collection = Collection(
            id=uuid4(),
            user_id=self.user_id,
            title=metadata['title'],
            description=f"Imported from ChatGPT on {datetime.now().isoformat()}",
            collection_type='conversation',
            source_platform='chatgpt',
            source_format='chatgpt_json',
            original_id=metadata['conversation_id'],
            import_date=datetime.now(),
            extra_metadata={
                'model_slug': metadata.get('model_slug'),
                'gizmo_id': metadata.get('gizmo_id'),
                'create_time': metadata.get('create_time'),
                'update_time': metadata.get('update_time')
            }
        )
        self.db.add(collection)

        # Import messages
        chunks_created = 0
        media_imported = 0
        embeddings_queued = 0

        # Track imported media to prevent duplicates
        imported_media_ids = set()

        for msg_data in messages:
            # Create message
            # Preserve original metadata including attachments
            preserved_metadata = {
                'author_name': msg_data.get('author_name'),
                'status': msg_data.get('status'),
                'weight': msg_data.get('weight'),
                'end_turn': msg_data.get('end_turn'),
                'recipient': msg_data.get('recipient')
            }

            # Include original metadata if present (attachments, gizmo_id, etc.)
            if msg_data.get('metadata'):
                original_meta = msg_data['metadata']
                if original_meta.get('attachments'):
                    preserved_metadata['attachments'] = original_meta['attachments']
                if original_meta.get('gizmo_id'):
                    preserved_metadata['gizmo_id'] = original_meta['gizmo_id']
                if original_meta.get('model_slug'):
                    preserved_metadata['model_slug'] = original_meta['model_slug']

            message = Message(
                id=uuid4(),
                collection_id=collection.id,
                user_id=self.user_id,
                sequence_number=msg_data['sequence_number'],
                role=msg_data['role'],
                message_type='standard',
                original_message_id=msg_data['node_id'],
                timestamp=datetime.fromtimestamp(msg_data['create_time']) if msg_data.get('create_time') else None,
                extra_metadata=preserved_metadata
            )
            self.db.add(message)

            # Create chunk for message content
            if msg_data['content']:
                # Sanitize content to remove null bytes and problematic characters
                sanitized_content = sanitize_text(msg_data['content'])

                chunk = await self.create_chunk(
                    message=message,
                    collection=collection,
                    content=sanitized_content,
                    chunk_level='document',
                    sequence=0,
                    is_summary=False,
                    queue_embedding=generate_embeddings
                )
                chunks_created += 1

                if generate_embeddings:
                    embeddings_queued += 1

            # Process attachments for this message
            # ALWAYS create Media records for ALL attachments, even if file not found
            if msg_data.get('metadata') and msg_data['metadata'].get('attachments'):
                for attachment in msg_data['metadata']['attachments']:
                    if not isinstance(attachment, dict):
                        continue

                    # Get attachment ID (the file reference)
                    attachment_id = attachment.get('id') or attachment.get('file_id')
                    if not attachment_id:
                        continue

                    # Skip if already imported (prevent duplicates)
                    if attachment_id in imported_media_ids:
                        continue

                    try:
                        # Try to find the actual file in archive
                        media_path = parser.find_media_file(attachment_id)

                        # Create Media record (even if file not found)
                        await self.import_media(
                            collection=collection,
                            message=message,
                            attachment_metadata=attachment,
                            media_path=media_path,  # May be None if not found
                            original_id=attachment_id
                        )
                        media_imported += 1
                        imported_media_ids.add(attachment_id)
                    except Exception as e:
                        logger.warning(f"Failed to import media {attachment_id}: {e}")

        return {
            'messages': len(messages),
            'chunks': chunks_created,
            'media': media_imported,
            'embeddings_queued': embeddings_queued
        }

    async def create_chunk(
        self,
        message: Message,
        collection: Collection,
        content: str,
        chunk_level: str,
        sequence: int,
        is_summary: bool = False,
        queue_embedding: bool = True
    ) -> Chunk:
        """
        Create a chunk and optionally queue for embedding.

        Args:
            message: Parent message
            collection: Parent collection
            content: Chunk content
            chunk_level: 'document', 'paragraph', or 'sentence'
            sequence: Chunk sequence number
            is_summary: Whether this is a summary chunk
            queue_embedding: Whether to queue for embedding generation

        Returns:
            Created chunk
        """
        chunk = Chunk(
            id=uuid4(),
            message_id=message.id,
            collection_id=collection.id,
            user_id=self.user_id,
            content=content,
            content_type='text',
            token_count=len(content.split()) * 1.3,  # Rough estimate
            chunk_level=chunk_level,
            chunk_sequence=sequence,
            is_summary=is_summary,
            extra_metadata={}
        )
        self.db.add(chunk)

        # Queue for embedding (will be picked up by batch processor)
        if queue_embedding:
            chunk.extra_metadata['embedding_queued'] = True
            chunk.extra_metadata['embedding_queued_at'] = datetime.now().isoformat()

        return chunk

    async def import_media(
        self,
        collection: Collection,
        original_id: str,
        attachment_metadata: Dict,
        message: Optional[Message] = None,
        media_path: Optional[Path] = None
    ) -> Media:
        """
        Import media file or create placeholder record.

        ALWAYS creates a Media record, even if the file is not found in the archive.
        This allows frontend to reference images by their original IDs and potentially
        upload missing files later.

        Args:
            collection: Parent collection
            original_id: Original media ID from ChatGPT (e.g., "file-XXXX")
            attachment_metadata: Attachment metadata from message (contains mime type, name, etc.)
            message: Optional parent message
            media_path: Source media file path (None if not found in archive)

        Returns:
            Created media object
        """
        # Extract metadata from attachment
        mime_type = attachment_metadata.get('mimeType') or attachment_metadata.get('mime_type')
        original_filename = attachment_metadata.get('name') or original_id

        # Determine media type from mime type
        # Must be one of: image, audio, video, document (database constraint)
        media_type = 'document'  # Default to document for unknown types
        if mime_type:
            if mime_type.startswith('image/'):
                media_type = 'image'
            elif mime_type.startswith('audio/'):
                media_type = 'audio'
            elif mime_type.startswith('video/'):
                media_type = 'video'
            elif mime_type.startswith('application/'):
                media_type = 'document'  # PDFs, docs, etc.

        # If file exists in archive, copy it
        storage_path_str = None
        blob_data = None
        file_size = attachment_metadata.get('size') or 0
        extra_metadata = {
            'source': 'chatgpt_archive',
            'imported_at': datetime.now().isoformat()
        }

        if media_path and media_path.exists():
            # File found - copy it with ORIGINAL ID as filename
            file_extension = media_path.suffix or self._guess_extension(mime_type)

            # Clean the original_id to make it filename-safe
            clean_id = original_id.replace('file-service://', '').replace('file://', '').replace('/', '_')

            # IMPORTANT: Store with ORIGINAL ID, no extra UUIDs
            storage_filename = f"{clean_id}{file_extension}"
            storage_path = self.media_storage_path / str(collection.id) / storage_filename

            # Create storage directory
            storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file to storage
            shutil.copy2(media_path, storage_path)
            storage_path_str = str(storage_path)

            # Read file for blob storage (optional, for small files)
            file_size = storage_path.stat().st_size
            if file_size < 10 * 1024 * 1024:  # Only store blobs < 10MB
                with open(storage_path, 'rb') as f:
                    blob_data = f.read()
        else:
            # File NOT found - create placeholder record
            extra_metadata['missing_from_archive'] = True
            extra_metadata['can_upload'] = True
            logger.info(f"Media file not found in archive: {original_id}, creating placeholder record")

        # Create media record (always, even if file not found)
        media = Media(
            id=uuid4(),
            collection_id=collection.id,
            message_id=message.id if message else None,
            user_id=self.user_id,
            media_type=media_type,
            mime_type=mime_type,
            original_filename=original_filename,
            is_archived=False,
            storage_path=storage_path_str,  # None if file not found
            blob_data=blob_data,  # None if file not found
            size_bytes=file_size,
            original_media_id=original_id,
            extra_metadata=extra_metadata
        )
        self.db.add(media)

        return media

    @staticmethod
    def _guess_extension(mime_type: str) -> str:
        """Guess file extension from MIME type."""
        mime_map = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/webp': '.webp',
            'image/gif': '.gif',
            'audio/wav': '.wav',
            'audio/mpeg': '.mp3',
            'video/mp4': '.mp4',
            'application/pdf': '.pdf'
        }
        return mime_map.get(mime_type, '.bin')


async def import_chatgpt_archive_task(
    db_session: AsyncSession,
    user_id: UUID,
    archive_path: Path,
    generate_embeddings: bool = True,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Async task for importing ChatGPT archive.

    This can be called from FastAPI background tasks or Celery.

    Args:
        db_session: Database session
        user_id: User ID
        archive_path: Path to archive
        generate_embeddings: Whether to generate embeddings
        progress_callback: Progress callback

    Returns:
        Import statistics
    """
    importer = ChatGPTImporter(db_session, user_id)
    return await importer.import_archive(
        archive_path,
        generate_embeddings=generate_embeddings,
        progress_callback=progress_callback
    )
