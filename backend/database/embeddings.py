"""Embedding generation service for vector search."""

import anthropic
from typing import List, Optional
import logging
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Claude or OpenAI."""

    def __init__(self):
        """Initialize embedding service."""
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.dimension = settings.embedding_dimension

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector, or None on error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None

        try:
            # For now, use a simple approach: create embeddings using Claude's text understanding
            # In production, you'd use a dedicated embedding model like Voyage AI or OpenAI

            # Placeholder: We'll use Claude to generate a semantic summary
            # and convert it to a vector using a hash-based approach
            # TODO: Replace with actual embedding API (Voyage AI, OpenAI, Cohere, etc.)

            return await self._generate_mock_embedding(text)

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def generate_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (or None for failed embeddings)
        """
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

    async def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate a mock embedding for development.

        This creates a deterministic but meaningless vector based on text hash.
        Replace with real embedding service in production.

        Args:
            text: Text to embed

        Returns:
            Mock embedding vector
        """
        # Use text hash to create deterministic vector
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(self.dimension).tolist()

        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = (np.array(embedding) / norm).tolist()

        return embedding

    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        if not embedding1 or not embedding2:
            return 0.0

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Global embedding service instance
embedding_service = EmbeddingService()


# Production embedding integration guide:
"""
To integrate a real embedding service, replace _generate_mock_embedding with:

1. Voyage AI (recommended for semantic search):
   ```python
   import voyageai
   vo = voyageai.Client(api_key="...")
   result = vo.embed([text], model="voyage-3")
   return result.embeddings[0]
   ```

2. OpenAI:
   ```python
   from openai import AsyncOpenAI
   client = AsyncOpenAI(api_key="...")
   response = await client.embeddings.create(
       input=text,
       model="text-embedding-3-small"
   )
   return response.data[0].embedding
   ```

3. Cohere:
   ```python
   import cohere
   co = cohere.Client(api_key="...")
   response = co.embed(texts=[text], model="embed-english-v3.0")
   return response.embeddings[0]
   ```
"""
