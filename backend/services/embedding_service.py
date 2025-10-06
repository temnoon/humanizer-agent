"""
Batch Embedding Generation Service

Generates embeddings for chunks using Ollama (local) or OpenAI (cloud).
Supports batch processing to avoid blocking imports.
"""

import asyncio
import httpx
import logging
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk_models import Chunk
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings."""

    def __init__(
        self,
        model: str = "mxbai-embed-large",  # Default local model
        dimension: int = 1024,
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize embedding service.

        Args:
            model: Embedding model name (mxbai-embed-large, nomic-embed-text, etc.)
            dimension: Embedding dimension (1024 for mxbai, 768 for nomic)
            ollama_url: Ollama API URL
        """
        self.model = model
        self.dimension = dimension
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector, or None if failed
        """
        if not text or len(text.strip()) < 3:
            logger.warning("Text too short for embedding")
            return None

        try:
            # Call Ollama API
            response = await self.client.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text[:8192]  # Limit to 8K chars
                }
            )

            if response.status_code == 200:
                data = response.json()
                embedding = data.get('embedding')

                if embedding and len(embedding) == self.dimension:
                    return embedding
                else:
                    logger.error(f"Unexpected embedding dimension: {len(embedding) if embedding else 0}")
                    return None
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 50
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of input texts
            batch_size: Number of embeddings to generate concurrently

        Returns:
            List of embedding vectors (None for failures)
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Generating embeddings for batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

            # Generate embeddings concurrently
            tasks = [self.generate_embedding(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            for j, emb in enumerate(batch_embeddings):
                if isinstance(emb, Exception):
                    logger.error(f"Embedding generation failed for item {i + j}: {emb}")
                    embeddings.append(None)
                else:
                    embeddings.append(emb)

            # Small delay to avoid overwhelming Ollama
            await asyncio.sleep(0.1)

        return embeddings

    async def process_queued_chunks(
        self,
        db_session: AsyncSession,
        batch_size: int = 100,
        max_chunks: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Process chunks that are queued for embedding generation.

        Args:
            db_session: Database session
            batch_size: Number of chunks to process at once
            max_chunks: Maximum number of chunks to process (None = all)

        Returns:
            Statistics about processing
        """
        stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'skipped': 0
        }

        # Find chunks with embedding_queued=true and embedding=null
        query = select(Chunk).where(
            and_(
                Chunk.embedding.is_(None),
                Chunk.extra_metadata['embedding_queued'].as_boolean().is_(True)
            )
        ).limit(max_chunks or 10000)

        result = await db_session.execute(query)
        chunks = result.scalars().all()

        if not chunks:
            logger.info("No chunks queued for embedding generation")
            return stats

        logger.info(f"Found {len(chunks)} chunks queued for embedding")

        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.content for chunk in batch]

            # Generate embeddings
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}")
            embeddings = await self.generate_embeddings_batch(texts, batch_size=50)

            # Update chunks
            for chunk, embedding in zip(batch, embeddings):
                stats['processed'] += 1

                if embedding:
                    chunk.embedding = embedding
                    chunk.embedding_model = self.model
                    chunk.embedding_generated_at = datetime.now()

                    # Remove queue flag
                    if chunk.extra_metadata and 'embedding_queued' in chunk.extra_metadata:
                        del chunk.extra_metadata['embedding_queued']
                        del chunk.extra_metadata['embedding_queued_at']

                    stats['succeeded'] += 1
                else:
                    stats['failed'] += 1
                    logger.warning(f"Failed to generate embedding for chunk {chunk.id}")

            # Commit batch
            await db_session.commit()
            logger.info(f"Committed batch {i // batch_size + 1}")

        logger.info(f"Embedding generation complete: {stats}")
        return stats

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


async def start_background_embedding_processor(
    db_session: AsyncSession,
    interval_seconds: int = 60,
    batch_size: int = 100
):
    """
    Background task that continuously processes queued embeddings.

    Args:
        db_session: Database session
        interval_seconds: How often to check for new chunks
        batch_size: Batch size for processing
    """
    service = EmbeddingService()
    logger.info("Starting background embedding processor")

    try:
        while True:
            try:
                stats = await service.process_queued_chunks(
                    db_session,
                    batch_size=batch_size
                )

                if stats['processed'] > 0:
                    logger.info(f"Processed {stats['processed']} chunks, "
                               f"{stats['succeeded']} succeeded, "
                               f"{stats['failed']} failed")

            except Exception as e:
                logger.error(f"Error in embedding processor: {e}", exc_info=True)

            # Wait before next iteration
            await asyncio.sleep(interval_seconds)

    finally:
        await service.close()


# Convenience function for manual processing
async def process_embeddings_now(
    db_session: AsyncSession,
    max_chunks: Optional[int] = None
) -> Dict[str, int]:
    """
    Process queued embeddings immediately (for API endpoint).

    Args:
        db_session: Database session
        max_chunks: Maximum number of chunks to process

    Returns:
        Processing statistics
    """
    service = EmbeddingService()
    try:
        return await service.process_queued_chunks(
            db_session,
            batch_size=100,
            max_chunks=max_chunks
        )
    finally:
        await service.close()
