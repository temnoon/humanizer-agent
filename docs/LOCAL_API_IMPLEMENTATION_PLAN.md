# Local API & Archive Database Implementation Plan

**Version:** 1.0
**Date:** October 2, 2025
**Status:** Ready for implementation
**Estimated Timeline:** 4 weeks

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Database Schema (PostgreSQL + pgvector)](#database-schema)
4. [Archive Parser System](#archive-parser-system)
5. [Media Handling Strategy](#media-handling-strategy)
6. [Ollama Integration](#ollama-integration)
7. [API Endpoints](#api-endpoints)
8. [Implementation Timeline](#implementation-timeline)
9. [Setup Instructions](#setup-instructions)
10. [Testing Strategy](#testing-strategy)

---

## Overview

### Goals

Implement a **local-first archive processing system** that:

1. ✅ Stores all data in **PostgreSQL with pgvector** for semantic search
2. ✅ Supports **ChatGPT and Claude conversation archives** (priority 1)
3. ✅ Supports **social network archives** (Facebook, Twitter, Instagram, Reddit)
4. ✅ Handles **media files** (audio, images, video) with filesystem storage + DB indexing
5. ✅ Uses **Ollama** for local AI transformations and embeddings
6. ✅ Maintains compatibility with existing transformation functionality
7. ✅ Enables **semantic search** across all archived conversations

### Why PostgreSQL + pgvector?

- **Native vector search**: No separate ChromaDB service needed
- **Transactional integrity**: Archive + embeddings + media references in atomic transactions
- **Production-ready**: No migration pain later
- **Join support**: Complex queries joining semantic search with metadata filters
- **Your expertise**: You already know PostgreSQL + pgvector well

### Priority Archive Types (First Iteration)

| Platform | Priority | Format | Media Support | Notes |
|----------|----------|--------|---------------|-------|
| **ChatGPT** | **P0** | conversations.json | Images, audio, (video) | Large files (100+ MB common) |
| **Claude** | **P0** | JSON export | Images, PDFs | Multi-turn conversations |
| Facebook | P1 | ZIP (JSON + HTML) | Photos, videos | Complex nested structure |
| Twitter/X | P1 | ZIP (JS files) | Images, videos | JavaScript format quirks |
| Instagram | P2 | ZIP (JSON) | Photos, videos | Future iteration |
| Reddit | P2 | ZIP (CSV/JSON) | Images, videos | Future iteration |

---

## Architecture Decisions

### 1. Database: PostgreSQL + pgvector

**Rationale**: Embeddings are core to archive functionality. PostgreSQL with pgvector provides:
- Single source of truth (no separate vector store)
- ACID transactions for archive uploads
- Native vector operations (faster than external ChromaDB)
- Production scalability without migration

**Pain Points & Mitigations**:

| Pain Point | Mitigation |
|------------|------------|
| Local setup complexity | Docker Compose one-command setup |
| Requires PostgreSQL installation | Document + provide Docker fallback |
| Connection pooling needed | SQLAlchemy async with pre-configured pools |
| Backup more complex than SQLite | Simple `pg_dump` scripts provided |

### 2. Media Storage: Filesystem + Database Metadata

**Rationale**: Media files (images, audio, video) stored on filesystem, metadata in database.

**Storage Structure**:
```
data/
├── archives/
│   ├── {archive_id}/
│   │   ├── raw/              # Original uploaded archive
│   │   │   └── conversations.json
│   │   └── media/            # Extracted media files
│   │       ├── images/
│   │       │   ├── {message_id}_img_001.png
│   │       │   └── {message_id}_img_002.jpg
│   │       ├── audio/
│   │       │   └── {message_id}_audio_001.mp3
│   │       └── video/
│   │           └── {message_id}_video_001.mp4
└── processed/
    └── {archive_id}/
        └── processing_log.json
```

**Database References**:
- `ParsedMessage.media` = JSON array of relative file paths
- `MediaFile` table tracks metadata (size, type, checksum, thumbnail path)

### 3. Ollama Integration: Local AI Processing

**Models Required**:
- **llama3.2:3b** - Text transformations, content analysis
- **nomic-embed-text** - Embeddings (768 dimensions) for semantic search

**Fallback Strategy**:
- Ollama unavailable → Use Claude API (existing functionality)
- Premium users → Prefer Claude API for higher quality
- Free users → Require Ollama for local processing

---

## Database Schema (PostgreSQL + pgvector)

### Core Tables

#### 1. `local_users` (Simple user tracking, no auth yet)

```sql
CREATE TABLE local_users (
    id VARCHAR PRIMARY KEY,
    name VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### 2. `archives` (Archive metadata)

```sql
CREATE TABLE archives (
    id VARCHAR PRIMARY KEY,
    platform VARCHAR NOT NULL,  -- 'chatgpt', 'claude', 'facebook', etc.
    user_id VARCHAR NOT NULL REFERENCES local_users(id),

    -- Source file info
    original_filename VARCHAR,
    original_size_bytes BIGINT,
    upload_path VARCHAR,  -- Path to original file in data/archives/{id}/raw/

    -- Date range
    date_range_start TIMESTAMP NOT NULL,
    date_range_end TIMESTAMP NOT NULL,

    -- Statistics
    total_messages INTEGER DEFAULT 0,
    total_media_files INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,

    -- Processing status
    upload_status VARCHAR DEFAULT 'processing',  -- processing, completed, failed
    processing_progress FLOAT DEFAULT 0.0,
    processing_error TEXT,

    -- Summary (flexible JSON)
    summary JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,

    INDEX idx_user_platform (user_id, platform),
    INDEX idx_upload_status (upload_status)
);
```

#### 3. `archive_messages` (Individual messages with embeddings)

```sql
CREATE TABLE archive_messages (
    id VARCHAR PRIMARY KEY,
    archive_id VARCHAR NOT NULL REFERENCES archives(id) ON DELETE CASCADE,

    -- Message identification
    platform VARCHAR NOT NULL,
    platform_message_id VARCHAR,  -- Original ID from platform
    timestamp TIMESTAMP NOT NULL,

    -- Author info
    author VARCHAR NOT NULL,
    author_role VARCHAR,  -- 'user', 'assistant', 'system' for ChatGPT/Claude

    -- Content
    content TEXT NOT NULL,
    content_type VARCHAR DEFAULT 'text',  -- 'text', 'code', 'image_description'

    -- Conversation threading
    conversation_id VARCHAR,
    parent_message_id VARCHAR,
    message_index INTEGER,  -- Order within conversation

    -- Media references (JSON array of paths)
    media JSONB,  -- [{"type": "image", "path": "...", "media_id": "..."}, ...]

    -- Platform-specific metadata
    metadata JSONB,

    -- Vector embedding for semantic search (768 dimensions for nomic-embed-text)
    embedding VECTOR(768),

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_archive_id (archive_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_author (author),
    INDEX idx_archive_timestamp (archive_id, timestamp),
    INDEX idx_archive_author (archive_id, author),
    INDEX idx_conversation (conversation_id),
    INDEX idx_parent_message (parent_message_id)
);

-- Vector index for semantic search (IVFFlat for fast approximate search)
CREATE INDEX idx_embedding ON archive_messages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### 4. `media_files` (Media file metadata and tracking)

```sql
CREATE TABLE media_files (
    id VARCHAR PRIMARY KEY,
    archive_id VARCHAR NOT NULL REFERENCES archives(id) ON DELETE CASCADE,
    message_id VARCHAR NOT NULL REFERENCES archive_messages(id) ON DELETE CASCADE,

    -- File info
    file_type VARCHAR NOT NULL,  -- 'image', 'audio', 'video'
    mime_type VARCHAR,  -- 'image/png', 'audio/mp3', etc.
    original_filename VARCHAR,

    -- Storage
    file_path VARCHAR NOT NULL,  -- Relative path from data/archives/
    file_size_bytes BIGINT,
    checksum VARCHAR,  -- SHA256 hash for deduplication

    -- Media metadata
    width INTEGER,  -- For images/videos
    height INTEGER,
    duration_seconds FLOAT,  -- For audio/video
    thumbnail_path VARCHAR,  -- Generated thumbnail for images/videos

    -- Platform-specific data
    metadata JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_archive_id (archive_id),
    INDEX idx_message_id (message_id),
    INDEX idx_file_type (file_type),
    INDEX idx_checksum (checksum)  -- For deduplication
);
```

#### 5. Existing `transformations` table (Updated)

```sql
-- Add user_id to existing transformations table
ALTER TABLE transformations ADD COLUMN user_id VARCHAR REFERENCES local_users(id);
CREATE INDEX idx_transformations_user ON transformations(user_id);
```

### pgvector Extension Setup

```sql
-- Enable pgvector extension (done in migration)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## Archive Parser System

### Base Parser Architecture

**File**: `backend/parsers/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
import hashlib


class ParsedMedia(BaseModel):
    """Media file reference."""
    type: str  # 'image', 'audio', 'video'
    original_path: str  # Path within archive
    content: Optional[bytes] = None  # Actual file content (extracted)
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ParsedMessage(BaseModel):
    """Standardized message format across all platforms."""
    id: str  # Unique identifier
    platform: str  # 'chatgpt', 'claude', 'facebook', etc.
    platform_message_id: Optional[str] = None  # Original ID from platform
    timestamp: datetime
    author: str
    author_role: Optional[str] = None  # 'user', 'assistant', 'system'
    content: str
    content_type: str = 'text'
    conversation_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    message_index: Optional[int] = None
    media: List[ParsedMedia] = []
    metadata: Dict[str, Any] = {}


class ParsedArchive(BaseModel):
    """Standardized archive format."""
    platform: str
    user: str  # Archive owner
    date_range: Tuple[datetime, datetime]  # (start, end)
    messages: List[ParsedMessage]
    total_media_files: int = 0
    summary: Dict[str, Any] = {}


class ArchiveParser(ABC):
    """Base class for platform-specific parsers."""

    platform_name: str = "unknown"

    def __init__(self):
        self.messages: List[ParsedMessage] = []

    @abstractmethod
    def detect_format(self, file_path: Path) -> bool:
        """
        Detect if file is valid archive for this platform.

        Returns True if this parser can handle the file.
        """
        pass

    @abstractmethod
    async def parse(self, file_path: Path) -> ParsedArchive:
        """
        Parse archive file into standardized format.

        Must be implemented by each platform parser.
        """
        pass

    def generate_id(self, content: str, timestamp: datetime) -> str:
        """Generate unique ID for message."""
        unique_string = f"{self.platform_name}_{timestamp.isoformat()}_{content[:100]}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

    def extract_date_range(self, messages: List[ParsedMessage]) -> Tuple[datetime, datetime]:
        """Extract earliest and latest dates from messages."""
        if not messages:
            now = datetime.now()
            return (now, now)

        timestamps = [msg.timestamp for msg in messages]
        return (min(timestamps), max(timestamps))

    def generate_summary(self, messages: List[ParsedMessage]) -> Dict[str, Any]:
        """Generate summary statistics."""
        media_count = sum(len(msg.media) for msg in messages)

        return {
            "total_messages": len(messages),
            "total_words": sum(len(msg.content.split()) for msg in messages),
            "date_range": self.extract_date_range(messages),
            "authors": list(set(msg.author for msg in messages)),
            "has_media": media_count > 0,
            "media_count": media_count
        }
```

### ChatGPT Conversation Parser

**File**: `backend/parsers/chatgpt.py`

```python
"""
ChatGPT conversation archive parser.

Supports:
- conversations.json format from ChatGPT export
- Large files (100+ MB)
- Streaming JSON parsing for memory efficiency
- Image attachments (DALL-E, uploaded images)
- Audio attachments (voice conversations)
- Code interpreter outputs
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import base64

from .base import ArchiveParser, ParsedMessage, ParsedArchive, ParsedMedia


class ChatGPTParser(ArchiveParser):
    """Parser for ChatGPT conversation exports."""

    platform_name = "chatgpt"

    def detect_format(self, file_path: Path) -> bool:
        """Detect ChatGPT conversations.json format."""
        if not file_path.suffix == '.json':
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first 1KB to check format
                sample = f.read(1024)

                # ChatGPT format typically starts with array of conversations
                # Check for characteristic fields
                return (
                    '"title"' in sample and
                    '"mapping"' in sample and
                    '"create_time"' in sample
                )
        except:
            return False

    async def parse(self, file_path: Path) -> ParsedArchive:
        """
        Parse ChatGPT conversations.json.

        Format structure:
        [
            {
                "title": "Conversation title",
                "create_time": 1234567890.123,
                "update_time": 1234567890.123,
                "mapping": {
                    "message_id": {
                        "id": "message_id",
                        "message": {
                            "id": "message_id",
                            "author": {"role": "user"},
                            "create_time": 1234567890.123,
                            "content": {
                                "content_type": "text",
                                "parts": ["message text"]
                            },
                            "metadata": {...}
                        },
                        "parent": "parent_message_id",
                        "children": ["child_id_1", "child_id_2"]
                    }
                },
                "current_node": "last_message_id"
            }
        ]
        """
        messages = []

        with open(file_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)

        for conversation in conversations:
            conversation_id = self._generate_conversation_id(conversation)
            conversation_title = conversation.get('title', 'Untitled')

            # Parse messages from mapping (tree structure)
            mapping = conversation.get('mapping', {})

            # Build message tree and extract linear conversation
            message_list = self._extract_messages_from_mapping(
                mapping=mapping,
                conversation_id=conversation_id,
                conversation_title=conversation_title
            )

            messages.extend(message_list)

        return ParsedArchive(
            platform="chatgpt",
            user="Unknown",  # ChatGPT exports don't include user info
            date_range=self.extract_date_range(messages),
            messages=messages,
            total_media_files=sum(len(msg.media) for msg in messages),
            summary=self.generate_summary(messages)
        )

    def _generate_conversation_id(self, conversation: Dict) -> str:
        """Generate stable conversation ID."""
        title = conversation.get('title', '')
        create_time = conversation.get('create_time', 0)
        return hashlib.sha256(f"{title}_{create_time}".encode()).hexdigest()[:16]

    def _extract_messages_from_mapping(
        self,
        mapping: Dict[str, Any],
        conversation_id: str,
        conversation_title: str
    ) -> List[ParsedMessage]:
        """
        Extract messages from ChatGPT's tree-based mapping structure.

        Follows the conversation flow from root to current_node.
        """
        messages = []

        for node_id, node in mapping.items():
            message_data = node.get('message')

            if not message_data:
                continue  # Skip empty nodes

            # Extract message content
            content = self._extract_content(message_data)

            if not content:
                continue  # Skip messages with no content

            # Parse timestamp
            create_time = message_data.get('create_time')
            if create_time:
                timestamp = datetime.fromtimestamp(create_time)
            else:
                timestamp = datetime.now()

            # Author info
            author_data = message_data.get('author', {})
            author_role = author_data.get('role', 'unknown')
            author_name = author_data.get('name', author_role)

            # Extract media (images, audio)
            media = self._extract_media(message_data)

            # Create message
            parsed_message = ParsedMessage(
                id=self.generate_id(content, timestamp),
                platform="chatgpt",
                platform_message_id=message_data.get('id'),
                timestamp=timestamp,
                author=author_name,
                author_role=author_role,
                content=content,
                content_type=self._get_content_type(message_data),
                conversation_id=conversation_id,
                parent_message_id=node.get('parent'),
                message_index=None,  # Will be set during final ordering
                media=media,
                metadata={
                    "conversation_title": conversation_title,
                    "model_slug": message_data.get('metadata', {}).get('model_slug'),
                    "finish_details": message_data.get('metadata', {}).get('finish_details'),
                    "weight": message_data.get('weight', 1.0)
                }
            )

            messages.append(parsed_message)

        # Order messages chronologically
        messages.sort(key=lambda m: m.timestamp)

        # Set message indices
        for i, msg in enumerate(messages):
            msg.message_index = i

        return messages

    def _extract_content(self, message_data: Dict) -> str:
        """Extract text content from message."""
        content_obj = message_data.get('content', {})

        if isinstance(content_obj, str):
            return content_obj

        content_type = content_obj.get('content_type', 'text')
        parts = content_obj.get('parts', [])

        if content_type == 'text':
            # Join all text parts
            return '\n'.join(str(part) for part in parts if part)

        elif content_type == 'code':
            # Code interpreter output
            return f"```\n{parts[0]}\n```" if parts else ""

        elif content_type == 'execution_output':
            # Code execution result
            return f"[Execution Output]\n{parts[0]}" if parts else ""

        else:
            # Other types (multimodal, etc.)
            return str(parts[0]) if parts else ""

    def _get_content_type(self, message_data: Dict) -> str:
        """Determine content type."""
        content_obj = message_data.get('content', {})

        if isinstance(content_obj, str):
            return 'text'

        return content_obj.get('content_type', 'text')

    def _extract_media(self, message_data: Dict) -> List[ParsedMedia]:
        """
        Extract media attachments (images, audio).

        ChatGPT media can be:
        - DALL-E generated images
        - Uploaded images
        - Voice conversation audio
        - File attachments
        """
        media = []

        # Check metadata for attachments
        metadata = message_data.get('metadata', {})
        attachments = metadata.get('attachments', [])

        for attachment in attachments:
            media_type = self._determine_media_type(attachment)

            if media_type:
                media.append(ParsedMedia(
                    type=media_type,
                    original_path=attachment.get('id', ''),
                    mime_type=attachment.get('mime_type'),
                    metadata={
                        "name": attachment.get('name'),
                        "size": attachment.get('size'),
                        "width": attachment.get('width'),
                        "height": attachment.get('height')
                    }
                ))

        # Check for DALL-E images in content
        content_obj = message_data.get('content', {})
        if isinstance(content_obj, dict):
            parts = content_obj.get('parts', [])
            for part in parts:
                if isinstance(part, dict) and 'asset_pointer' in part:
                    # DALL-E image
                    media.append(ParsedMedia(
                        type='image',
                        original_path=part.get('asset_pointer', ''),
                        metadata={
                            "source": "dalle",
                            "prompt": part.get('metadata', {}).get('dalle', {}).get('prompt')
                        }
                    ))

        return media

    def _determine_media_type(self, attachment: Dict) -> Optional[str]:
        """Determine media type from attachment."""
        mime_type = attachment.get('mime_type', '')

        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('video/'):
            return 'video'
        else:
            return None
```

### Claude Conversation Parser

**File**: `backend/parsers/claude.py`

```python
"""
Claude conversation archive parser.

Supports:
- Claude.ai web interface JSON exports
- Projects and artifacts
- Image attachments
- PDF attachments
- Multi-turn conversations
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from .base import ArchiveParser, ParsedMessage, ParsedArchive, ParsedMedia


class ClaudeParser(ArchiveParser):
    """Parser for Claude conversation exports."""

    platform_name = "claude"

    def detect_format(self, file_path: Path) -> bool:
        """Detect Claude conversation format."""
        if not file_path.suffix == '.json':
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Check for Claude-specific fields
                if isinstance(data, dict):
                    return (
                        'uuid' in data or
                        'chat_messages' in data or
                        ('name' in data and 'messages' in data)
                    )
                elif isinstance(data, list):
                    # Array of conversations
                    if data and isinstance(data[0], dict):
                        return 'uuid' in data[0] or 'messages' in data[0]
        except:
            return False

        return False

    async def parse(self, file_path: Path) -> ParsedArchive:
        """
        Parse Claude conversation export.

        Format can vary:
        1. Single conversation object
        2. Array of conversations
        3. Project export with artifacts
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = []

        # Handle different export formats
        if isinstance(data, list):
            # Multiple conversations
            for conversation in data:
                messages.extend(self._parse_conversation(conversation))
        else:
            # Single conversation
            messages.extend(self._parse_conversation(data))

        return ParsedArchive(
            platform="claude",
            user=data.get('user_id', 'Unknown') if isinstance(data, dict) else 'Unknown',
            date_range=self.extract_date_range(messages),
            messages=messages,
            total_media_files=sum(len(msg.media) for msg in messages),
            summary=self.generate_summary(messages)
        )

    def _parse_conversation(self, conversation: Dict) -> List[ParsedMessage]:
        """Parse a single Claude conversation."""
        messages = []

        conversation_id = conversation.get('uuid', conversation.get('id', 'unknown'))
        conversation_name = conversation.get('name', 'Untitled')

        # Extract messages array
        message_list = conversation.get('chat_messages', conversation.get('messages', []))

        for i, msg in enumerate(message_list):
            # Parse content
            content = self._extract_content(msg)

            if not content:
                continue

            # Parse timestamp
            timestamp = self._parse_timestamp(msg)

            # Author info
            sender = msg.get('sender', msg.get('role', 'unknown'))

            # Extract media
            media = self._extract_media(msg)

            parsed_message = ParsedMessage(
                id=self.generate_id(content, timestamp),
                platform="claude",
                platform_message_id=msg.get('uuid', msg.get('id')),
                timestamp=timestamp,
                author=sender,
                author_role=sender,  # 'user' or 'assistant'
                content=content,
                conversation_id=conversation_id,
                message_index=i,
                media=media,
                metadata={
                    "conversation_name": conversation_name,
                    "model": conversation.get('model'),
                    "project_uuid": conversation.get('project_uuid'),
                    "attachments": msg.get('attachments', [])
                }
            )

            messages.append(parsed_message)

        return messages

    def _extract_content(self, message: Dict) -> str:
        """Extract text content from Claude message."""
        # Try different content field names
        content = message.get('text', message.get('content'))

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            # Multi-part content (text + images)
            text_parts = []
            for part in content:
                if isinstance(part, dict):
                    if part.get('type') == 'text':
                        text_parts.append(part.get('text', ''))
                elif isinstance(part, str):
                    text_parts.append(part)
            return '\n'.join(text_parts)

        return str(content) if content else ""

    def _parse_timestamp(self, message: Dict) -> datetime:
        """Parse timestamp from Claude message."""
        # Try different timestamp fields
        timestamp_str = (
            message.get('created_at') or
            message.get('timestamp') or
            message.get('sent_at')
        )

        if timestamp_str:
            try:
                # Handle ISO format
                if isinstance(timestamp_str, str):
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Handle Unix timestamp
                elif isinstance(timestamp_str, (int, float)):
                    return datetime.fromtimestamp(timestamp_str)
            except:
                pass

        return datetime.now()

    def _extract_media(self, message: Dict) -> List[ParsedMedia]:
        """Extract media attachments from Claude message."""
        media = []

        # Check attachments
        attachments = message.get('attachments', [])
        for attachment in attachments:
            file_name = attachment.get('file_name', '')
            file_type = attachment.get('file_type', '')

            # Determine media type
            if file_type.startswith('image/') or file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                media_type = 'image'
            elif file_name.lower().endswith('.pdf'):
                media_type = 'document'
            else:
                media_type = 'file'

            media.append(ParsedMedia(
                type=media_type,
                original_path=attachment.get('id', file_name),
                mime_type=file_type,
                metadata={
                    "file_name": file_name,
                    "file_size": attachment.get('file_size'),
                    "extracted_content": attachment.get('extracted_content')
                }
            ))

        # Check content for image references
        content = message.get('content', [])
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get('type') == 'image':
                    media.append(ParsedMedia(
                        type='image',
                        original_path=part.get('source', {}).get('url', ''),
                        metadata=part.get('source', {})
                    ))

        return media
```

---

## Media Handling Strategy

### Media Extraction & Storage Service

**File**: `backend/services/media_service.py`

```python
"""
Media extraction and storage service.

Handles:
- Extracting media from archive uploads
- Storing files in organized filesystem structure
- Generating thumbnails for images/videos
- Computing checksums for deduplication
- Creating database records
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from models.archive import MediaFile
from parsers.base import ParsedMedia
from config import settings


class MediaService:
    """Handle media file extraction and storage."""

    def __init__(self, archive_id: str):
        self.archive_id = archive_id
        self.base_path = Path(settings.archives_dir) / archive_id / "media"

        # Create directory structure
        self.images_path = self.base_path / "images"
        self.audio_path = self.base_path / "audio"
        self.video_path = self.base_path / "video"
        self.thumbnails_path = self.base_path / "thumbnails"

        for path in [self.images_path, self.audio_path, self.video_path, self.thumbnails_path]:
            path.mkdir(parents=True, exist_ok=True)

    async def store_media(
        self,
        message_id: str,
        media: ParsedMedia,
        media_index: int,
        db: AsyncSession
    ) -> Optional[MediaFile]:
        """
        Store media file and create database record.

        Args:
            message_id: ID of message this media belongs to
            media: ParsedMedia object with content
            media_index: Index of media within message (for filename)
            db: Database session

        Returns:
            MediaFile database record or None if storage failed
        """
        if not media.content:
            return None

        # Determine storage path
        file_extension = self._get_extension(media)
        filename = f"{message_id}_{media.type}_{media_index:03d}{file_extension}"

        if media.type == 'image':
            file_path = self.images_path / filename
        elif media.type == 'audio':
            file_path = self.audio_path / filename
        elif media.type == 'video':
            file_path = self.video_path / filename
        else:
            file_path = self.base_path / filename

        # Write file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(media.content)

        # Compute checksum
        checksum = self._compute_checksum(media.content)

        # Get file size
        file_size = len(media.content)

        # Generate thumbnail for images/videos
        thumbnail_path = None
        width, height = None, None

        if media.type == 'image':
            thumbnail_path, width, height = await self._create_image_thumbnail(
                file_path,
                message_id,
                media_index
            )
        elif media.type == 'video':
            # Video thumbnail generation would go here
            # Requires ffmpeg integration
            pass

        # Create database record
        relative_path = str(file_path.relative_to(settings.archives_dir))

        media_file = MediaFile(
            id=f"{message_id}_media_{media_index}",
            archive_id=self.archive_id,
            message_id=message_id,
            file_type=media.type,
            mime_type=media.mime_type or self._guess_mime_type(file_path),
            original_filename=media.metadata.get('name', filename),
            file_path=relative_path,
            file_size_bytes=file_size,
            checksum=checksum,
            width=width,
            height=height,
            thumbnail_path=thumbnail_path,
            metadata=media.metadata
        )

        db.add(media_file)
        await db.commit()

        return media_file

    def _get_extension(self, media: ParsedMedia) -> str:
        """Determine file extension from mime type or metadata."""
        if media.mime_type:
            ext = mimetypes.guess_extension(media.mime_type)
            if ext:
                return ext

        # Try to get from original filename
        original = media.metadata.get('name', media.metadata.get('file_name', ''))
        if original:
            return Path(original).suffix

        # Default extensions by type
        defaults = {
            'image': '.png',
            'audio': '.mp3',
            'video': '.mp4'
        }
        return defaults.get(media.type, '.bin')

    def _compute_checksum(self, content: bytes) -> str:
        """Compute SHA256 checksum for deduplication."""
        return hashlib.sha256(content).hexdigest()

    def _guess_mime_type(self, file_path: Path) -> Optional[str]:
        """Guess MIME type from file extension."""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type

    async def _create_image_thumbnail(
        self,
        image_path: Path,
        message_id: str,
        media_index: int,
        max_size: Tuple[int, int] = (300, 300)
    ) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        Create thumbnail for image.

        Returns:
            (thumbnail_relative_path, original_width, original_height)
        """
        try:
            # Open image
            with Image.open(image_path) as img:
                original_width, original_height = img.size

                # Create thumbnail
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save thumbnail
                thumbnail_filename = f"{message_id}_thumb_{media_index:03d}.jpg"
                thumbnail_path = self.thumbnails_path / thumbnail_filename

                # Convert to RGB if necessary (for PNG with alpha)
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img

                img.save(thumbnail_path, 'JPEG', quality=85)

                relative_path = str(thumbnail_path.relative_to(settings.archives_dir))
                return relative_path, original_width, original_height

        except Exception as e:
            print(f"Failed to create thumbnail: {e}")
            return None, None, None

    async def check_duplicate(
        self,
        checksum: str,
        db: AsyncSession
    ) -> Optional[MediaFile]:
        """
        Check if media file already exists (by checksum).

        Enables deduplication of identical files.
        """
        from sqlalchemy import select

        result = await db.execute(
            select(MediaFile).where(MediaFile.checksum == checksum)
        )
        return result.scalar_one_or_none()
```

### Media API Endpoints

Add to archive routes:

```python
@router.get("/archives/{archive_id}/media/{media_id}")
async def get_media_file(archive_id: str, media_id: str):
    """
    Serve media file.

    Returns actual file content for images, audio, video.
    """
    # Get media record from database
    media = await db.get(MediaFile, media_id)

    if not media or media.archive_id != archive_id:
        raise HTTPException(status_code=404, detail="Media not found")

    # Serve file
    file_path = Path(settings.archives_dir) / media.file_path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        file_path,
        media_type=media.mime_type,
        filename=media.original_filename
    )


@router.get("/archives/{archive_id}/media/{media_id}/thumbnail")
async def get_media_thumbnail(archive_id: str, media_id: str):
    """Get thumbnail for image/video."""
    media = await db.get(MediaFile, media_id)

    if not media or not media.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    thumbnail_path = Path(settings.archives_dir) / media.thumbnail_path

    return FileResponse(
        thumbnail_path,
        media_type="image/jpeg"
    )
```

---

## Ollama Integration

### Ollama Service

**File**: `backend/services/ollama_service.py`

```python
"""Ollama local LLM integration."""

import httpx
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

from config import settings


class OllamaService:
    """
    Service for interacting with Ollama local LLM.

    Ollama must be running separately (installed from ollama.ai).
    """

    def __init__(self):
        self.host = settings.ollama_host
        self.default_model = settings.ollama_default_model
        self.embedding_model = settings.ollama_embedding_model
        self.client = httpx.AsyncClient(timeout=300.0)

    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = await self.client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except:
            return False

    async def list_models(self) -> List[str]:
        """List installed models."""
        try:
            response = await self.client.get(f"{self.host}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except:
            return []

    async def embed(
        self,
        text: str,
        model: str = None
    ) -> List[float]:
        """
        Generate embeddings for text.

        Returns 768-dimensional vector for nomic-embed-text.
        Compatible with pgvector VECTOR(768) column.
        """
        model = model or self.embedding_model

        response = await self.client.post(
            f"{self.host}/api/embeddings",
            json={
                "model": model,
                "prompt": text
            }
        )

        result = response.json()
        return result.get("embedding", [])

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """
        Chat completion with conversation history.

        Args:
            messages: [{"role": "user", "content": "..."}]
            model: Model name
            temperature: Sampling temperature
            stream: If True, return generator for streaming
        """
        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }

        if stream:
            return self._stream_chat(payload)
        else:
            response = await self.client.post(
                f"{self.host}/api/chat",
                json=payload
            )
            result = response.json()
            return result.get("message", {}).get("content", "")

    async def _stream_chat(self, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        async with self.client.stream(
            "POST",
            f"{self.host}/api/chat",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data:
                        content = data["message"].get("content", "")
                        if content:
                            yield content
```

### Vector Search Service (PostgreSQL pgvector)

**File**: `backend/services/vector_service.py`

```python
"""PostgreSQL pgvector semantic search service."""

from typing import List, Dict, Any
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.archive import ParsedMessage
from services.ollama_service import OllamaService


class VectorSearchService:
    """Semantic search using PostgreSQL pgvector."""

    def __init__(self):
        self.ollama = OllamaService()

    async def embed_and_store(
        self,
        message: ParsedMessage,
        db: AsyncSession
    ):
        """Generate embedding and store in message record."""
        # Generate embedding
        embedding = await self.ollama.embed(message.content)

        # Store in database
        message.embedding = embedding
        await db.commit()

    async def batch_embed_archive(
        self,
        archive_id: str,
        db: AsyncSession,
        batch_size: int = 100
    ):
        """Generate embeddings for all messages in archive."""
        # Get messages without embeddings
        stmt = select(ParsedMessage).where(
            ParsedMessage.archive_id == archive_id,
            ParsedMessage.embedding.is_(None)
        ).limit(batch_size)

        while True:
            result = await db.execute(stmt)
            messages = result.scalars().all()

            if not messages:
                break

            for message in messages:
                await self.embed_and_store(message, db)

    async def search(
        self,
        query: str,
        archive_id: str,
        limit: int = 10,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector similarity.

        Uses cosine distance for similarity.
        """
        # Generate query embedding
        query_embedding = await self.ollama.embed(query)

        # Vector search with pgvector
        stmt = text("""
            SELECT
                id, content, author, timestamp, metadata,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM archive_messages
            WHERE archive_id = :archive_id
              AND embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        result = await db.execute(
            stmt,
            {
                "query_embedding": query_embedding,
                "archive_id": archive_id,
                "limit": limit
            }
        )

        return [
            {
                "id": row.id,
                "content": row.content,
                "author": row.author,
                "timestamp": row.timestamp,
                "metadata": row.metadata,
                "similarity": row.similarity
            }
            for row in result.fetchall()
        ]
```

---

## API Endpoints

### Archive Upload & Management

**File**: `backend/api/archive_routes.py`

```python
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/archives", tags=["archives"])


@router.post("/upload")
async def upload_archive(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process archive file.

    Supports:
    - ChatGPT conversations.json (large files)
    - Claude conversation exports
    - Facebook, Twitter ZIP archives

    Processing happens in background.
    """
    # Validate file size
    # Auto-detect format
    # Save to data/archives/{id}/raw/
    # Start background processing
    pass


@router.get("/{archive_id}/status")
async def get_archive_status(archive_id: str):
    """Get processing status and progress."""
    pass


@router.get("/{archive_id}")
async def get_archive_info(archive_id: str):
    """Get archive metadata and summary."""
    pass


@router.get("/{archive_id}/messages")
async def get_archive_messages(
    archive_id: str,
    limit: int = 50,
    offset: int = 0,
    author: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get paginated messages with filters."""
    pass


@router.post("/{archive_id}/search")
async def search_archive(
    archive_id: str,
    query: str,
    limit: int = 10
):
    """Semantic search within archive."""
    pass


@router.delete("/{archive_id}")
async def delete_archive(archive_id: str):
    """Delete archive and all associated data."""
    pass
```

---

## Implementation Timeline

### Week 1: PostgreSQL Foundation & ChatGPT Parser

**Days 1-2: PostgreSQL Setup**
- Docker Compose with ankane/pgvector image
- Database schema design
- Alembic migration for archive tables
- Connection pooling setup
- Startup health checks

**Days 3-4: ChatGPT Parser**
- Base parser architecture
- ChatGPT conversations.json parser
- Handle large files (streaming JSON)
- Media extraction (images, audio)
- Unit tests with sample exports

**Day 5: Media Service**
- Media extraction and storage
- Thumbnail generation
- Checksum-based deduplication
- Database record creation

### Week 2: Claude Parser & Ollama Integration

**Days 1-2: Claude Parser**
- Claude conversation JSON parser
- Handle different export formats
- Image and PDF attachment support
- Conversation threading

**Days 3-4: Ollama Service**
- HTTP client for Ollama API
- Embeddings (nomic-embed-text)
- Chat completions
- Model availability checks
- Graceful fallback to Claude API

**Day 5: Vector Search**
- VectorSearchService implementation
- pgvector integration
- Batch embedding generation
- Search endpoint

### Week 3: Archive API & Processing

**Days 1-2: Upload Endpoint**
- File upload handling
- Format auto-detection
- Background processing tasks
- Progress tracking

**Days 3-4: Archive Management**
- Get archive info endpoint
- Message listing with pagination
- Filtering by author, date range
- Delete archive endpoint

**Day 5: Search & Integration**
- Semantic search endpoint
- Pattern detection basics
- Integration testing

### Week 4: Social Network Parsers & Polish

**Days 1-2: Facebook Parser**
- ZIP extraction
- JSON message parsing
- Photo/video extraction
- Encoding fixes (Latin-1 issue)

**Days 3: Twitter Parser**
- JS file parsing (tweets.js format)
- DM extraction
- Media handling

**Days 4-5: Testing & Documentation**
- End-to-end integration tests
- Performance optimization
- API documentation
- Setup guide for new developers

---

## Setup Instructions

### Prerequisites

```bash
# PostgreSQL with pgvector
brew install postgresql@16  # macOS

# Or use Docker (recommended)
docker --version
docker-compose --version

# Ollama (optional, for local AI)
curl https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Quick Start

1. **Clone and setup**:
```bash
cd humanizer-agent
cp backend/.env.example backend/.env
# Edit .env with your API keys
```

2. **Start PostgreSQL**:
```bash
docker-compose up -d postgres
```

3. **Run migrations**:
```bash
cd backend
alembic upgrade head
```

4. **Start backend**:
```bash
python main.py
```

5. **Verify setup**:
```bash
curl http://localhost:8000/health
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://humanizer:dev_password@localhost:5432/humanizer_local
DATABASE_POOL_SIZE=10

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Archives
MAX_UPLOAD_SIZE_MB=500
ARCHIVES_DIR=data/archives
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_parsers/test_chatgpt.py
async def test_chatgpt_parser_large_file():
    """Test parsing 100+ MB conversations.json."""
    pass

async def test_chatgpt_media_extraction():
    """Test image and audio extraction."""
    pass

# tests/test_parsers/test_claude.py
async def test_claude_parser_multi_conversation():
    """Test parsing multiple conversations."""
    pass

# tests/test_services/test_vector_search.py
async def test_embedding_generation():
    """Test Ollama embedding generation."""
    pass

async def test_semantic_search():
    """Test pgvector search accuracy."""
    pass

# tests/test_services/test_media.py
async def test_media_storage():
    """Test media file storage and thumbnail generation."""
    pass

async def test_media_deduplication():
    """Test checksum-based deduplication."""
    pass
```

### Integration Tests

```python
# tests/integration/test_archive_upload.py
async def test_full_chatgpt_upload():
    """
    End-to-end test:
    1. Upload conversations.json
    2. Process in background
    3. Verify all messages stored
    4. Verify embeddings generated
    5. Verify media extracted
    6. Test semantic search
    """
    pass
```

### Performance Benchmarks

- Upload 500 MB conversations.json: < 5 minutes
- Parse 10,000 messages: < 2 minutes
- Generate embeddings (10,000 messages): < 10 minutes
- Semantic search (10,000 messages): < 1 second

---

## Success Metrics

After implementation, verify:

1. ✅ **PostgreSQL + pgvector working**
   - Extension installed
   - Vector indexes created
   - Connection pooling functional

2. ✅ **ChatGPT archives supported**
   - Large conversations.json files (100+ MB)
   - Images extracted and stored
   - Audio files handled
   - Embeddings generated

3. ✅ **Claude archives supported**
   - JSON exports parsed
   - Multi-conversation support
   - Image/PDF attachments stored

4. ✅ **Media handling complete**
   - Files stored in organized structure
   - Thumbnails generated for images
   - Database metadata accurate
   - Deduplication working

5. ✅ **Semantic search working**
   - Ollama embeddings generated
   - pgvector search returns relevant results
   - Sub-second query performance

6. ✅ **API functional**
   - Upload endpoint handles large files
   - Background processing tracks progress
   - Search endpoint returns ranked results
   - Media files served correctly

7. ✅ **Existing features preserved**
   - Transformation API still works
   - Claude Agent SDK integration intact
   - Frontend compatibility maintained

---

## Next Steps After This Phase

### Phase 2 (Weeks 5-6): Browser Extension
- Download detection for archive files
- One-click import to local API
- Platform-specific extraction helpers

### Phase 3 (Weeks 7-8): Electron Desktop App
- Embedded local API server
- Ollama installation helper
- Model download UI
- System tray integration

### Phase 4 (Weeks 9-10): Additional Parsers
- Instagram JSON parser
- Reddit CSV/JSON parser
- LinkedIn exports
- Generic text/markdown import

### Phase 5 (Weeks 11-14): Production Features (from PRODUCTION_ROADMAP.md)
- Full authentication system
- Stripe subscription integration
- Usage tracking and limits
- Email notifications

---

## File Checklist

Before starting implementation, ensure these files exist:

### New Files to Create

**Database**:
- [ ] `backend/models/archive.py` - Archive and message models
- [ ] `backend/models/media.py` - Media file model
- [ ] `backend/models/user.py` - Simple user model
- [ ] `alembic/versions/001_postgresql_initial.py` - Initial migration

**Services**:
- [ ] `backend/services/ollama_service.py` - Ollama integration
- [ ] `backend/services/vector_service.py` - pgvector search
- [ ] `backend/services/media_service.py` - Media handling
- [ ] `backend/services/archive_service.py` - Archive orchestration

**Parsers**:
- [ ] `backend/parsers/base.py` - Base parser class
- [ ] `backend/parsers/chatgpt.py` - ChatGPT parser
- [ ] `backend/parsers/claude.py` - Claude parser
- [ ] `backend/parsers/facebook.py` - Facebook parser (week 4)
- [ ] `backend/parsers/twitter.py` - Twitter parser (week 4)

**API**:
- [ ] `backend/api/archive_routes.py` - Archive endpoints

**Infrastructure**:
- [ ] `docker-compose.yml` - PostgreSQL + pgvector
- [ ] `init-scripts/01-init-pgvector.sql` - Database init
- [ ] `start-local.sh` - Local development script

**Configuration**:
- [ ] Update `backend/config.py` - Add PostgreSQL, Ollama, archive settings

### Files to Modify

- [ ] `backend/main.py` - Add archive routes, health checks
- [ ] `backend/requirements.txt` - Add dependencies
- [ ] `backend/.env.example` - Add new environment variables

---

## Dependencies to Add

```txt
# PostgreSQL + Vector
asyncpg==0.29.0
psycopg2-binary==2.9.9
pgvector==0.2.5
alembic==1.13.1

# Ollama
httpx==0.27.0

# Archive Processing
python-multipart==0.0.9
aiofiles==24.1.0
beautifulsoup4==4.12.3
python-magic==0.4.27

# Media Processing
Pillow==10.2.0

# Existing dependencies
fastapi
uvicorn
sqlalchemy
pydantic
pydantic-settings
anthropic
```

---

## Important Notes for Next Session

1. **PostgreSQL First**: Set up PostgreSQL + pgvector before anything else
2. **ChatGPT Priority**: Implement ChatGPT parser before social networks
3. **Media is Core**: Don't skip media handling - it's essential for ChatGPT/Claude archives
4. **Large Files**: Test with real 100+ MB conversations.json files early
5. **Embeddings**: Batch embed after initial import (don't block upload)
6. **Ollama Optional**: System should work without Ollama (Claude API fallback)
7. **Keep Existing Code**: Don't break current transformation functionality

---

## Questions to Resolve During Implementation

1. **Embedding Strategy**: Generate embeddings during upload or lazily on first search?
   - **Recommendation**: Background task after upload completes

2. **Media Download**: Download ChatGPT media from URLs or expect in export?
   - **Note**: ChatGPT exports include media references but may need fetching

3. **Conversation Threading**: How to display branching conversations (ChatGPT trees)?
   - **Recommendation**: Flatten to chronological + store parent_id for UI

4. **Deduplication**: Dedupe at media level or message level?
   - **Recommendation**: Media only (messages usually unique)

---

**This document should be your primary reference when implementing the local API and archive database system. All architecture decisions and implementation details are documented here.**
